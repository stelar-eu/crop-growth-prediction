import os
import glob
import sys
import datetime as dt
from sentinelhub import CRS
from typing import List, Text, Tuple
from stelar_spatiotemporal.preprocessing.preprocessing import combine_npys_into_eopatches
from stelar_spatiotemporal.preprocessing.vista_preprocessing import unpack_vista_reflectance
from stelar_spatiotemporal.segmentation.bands_data_package import BandsDataPackage
from stelar_spatiotemporal.segmentation.segmentation import *
import warnings
warnings.filterwarnings("ignore")

def parse_args(args:List[str]) -> dict:
    optionals = ["-sdates"]

    # Parse required arguments
    bands_data_package, out_path, model_path = parse_required_args(args)

    # Check if unknown optional arguments are given
    for arg in args[1:]:
        if arg.startswith("-"):
            if arg not in optionals:
                print("Unknown argument: {}".format(arg))
                sys.exit(1)

    # Parse the segment dates if necessary
    sdates = parse_sdates(args)

    # Create the dictionary with the arguments
    args_dict = {"bands_data_package": bands_data_package,
                    "out_path": out_path,
                    "model_path": model_path,
                    "sdates": sdates}
    
    print("Arguments: {}".format(args_dict))
    
    return args_dict

def parse_required_args(args) -> Tuple[BandsDataPackage, Text, Text]:
    required_args = ["b2_path", "b3_path", "b4_path", "b8a_path", "out_path", "model_path"]

    # Look if necessary arguments are given
    if len(args) < len(required_args) + 1:
        print("Please give the following required arguments (in that order and format): {}".format(required_args))
        sys.exit(1)

    # Parse the required arguments
    for arg, arg_name in zip(args[:len(required_args)], required_args):
        if arg.startswith("-"):
            print("Please give the following required arguments (in that order and format): {}".format(required_args))
            sys.exit(1)
        else:
            if arg_name == "b2_path":
                b2_path = arg
            elif arg_name == "b3_path":
                b3_path = arg
            elif arg_name == "b4_path":
                b4_path = arg
            elif arg_name == "b8a_path":
                b8a_path = arg
            elif arg_name == "out_path":
                out_path = arg
            elif arg_name == "model_path":
                model_path = arg

    bands_data_package = BandsDataPackage(b2_path=b2_path,
                                          b3_path=b3_path,
                                          b4_path=b4_path,
                                          b8_path=b8a_path,
                                          file_extension="RAS")
    return bands_data_package, out_path, model_path


def parse_sdates(args) -> List[dt.datetime]:
    """
    Parse the segment dates from the arguments
    """

    # Look if specific dates are given
    sdates_id = args.index("-sdates")
    if sdates_id != -1:
        if len(args) < sdates_id + 2:
            print("Please give specific dates in the format YYYY-MM-DD after the -sdates flag")
            sys.exit(1)

        sdates = args[sdates_id+1].split(",")

        # Parse the dates
        try:
            sdates = [dt.datetime.strptime(date, "%Y-%m-%d") for date in sdates]
        except ValueError:
            print("Dates should be given in the format YYYY-MM-DD")
            sys.exit(1)

        return sdates
    else:
        return None

def cleanup(*args):
    for todel_path in args:
        if os.path.exists(todel_path):
            print("Deleting {}".format(todel_path))
            os.system("rm -rf {}".format(todel_path))


def segmentation_pipeline(bands_data_package:BandsDataPackage, out_path:Text, model_path:Text, sdates:List[dt.datetime] = None):
    """
    Pipeline for segmenting a Sentinel-2 tile using a pre-trained ResUNet model.

    Parameters
    ----------
    bands_data_package : BandsDataPackage
        Data package containing the paths to the RAS files with RGBNIR bands
    out_path : Text
        Path to the output shapefile
    model_path : Text
        Path to the pre-trained ResUNet model
    sdates : List[dt.datetime], optional
        List of dates to segment, by default None (segment all overlapping dates in the RAS files)
    """
    
    TMPDIR = '/tmp'
        
    # 1. # Unpacks RAS and RHD files into numpy arrays
    print("1. Unpacking RAS files...")
    npy_dir = os.path.join(TMPDIR, "npys")
    unpack_vista_reflectance(bands_data_package, outdir=npy_dir, crs=CRS(32630)) 

    # Create band data package with local paths
    b2_path = os.path.join(npy_dir, "B2")
    b3_path = os.path.join(npy_dir, "B3")
    b4_path = os.path.join(npy_dir, "B4")
    b8_path = os.path.join(npy_dir, "B8A")
    npy_data_package = BandsDataPackage(b2_path, b3_path, b4_path, b8_path, file_extension="npy")

    # 2. Combining the images into one eopatch
    print("2. Combining images into one eopatch...")
    eopatches_dir = os.path.join(TMPDIR, "segment_eopatch")
    eop_path = combine_rgb_npys_into_eopatch(npy_data_package, outdir=eopatches_dir, dates=sdates)

    # 3. Splitting the eopatch into patchlets
    print("3. Splitting eopatch into patchlets...")
    plet_dir = os.path.join(TMPDIR, "patchlets")
    patchify_segmentation_data(eop_path, outdir=plet_dir, n_jobs=1)

    # 4. Run segmentation
    print("4. Running segmentation...")
    segment_patchlets(model_path, plet_dir)

    # 5. Vectorize segmentation
    print("5. Vectorizing segmentation...")
    vecs_dir = os.path.join(TMPDIR, "contours")
    vectorize_patchlets(plet_dir, outdir=vecs_dir)

    # 6. Combine patchlets shapes single shapefile
    print("6. Combining patchlet shapes into single shapefile...")
    combine_patchlet_shapes(vecs_dir, out_path)

    # 7. Cleanup
    print("7. Cleaning up...")
    cleanup(npy_dir, eopatches_dir, plet_dir, vecs_dir)
    

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 0:
        args = [
            "s3://stelar-spatiotemporal/RGB/B2",
            "s3://stelar-spatiotemporal/RGB/B2",
            "s3://stelar-spatiotemporal/RGB/B2",
            "s3://stelar-spatiotemporal/RGB/B2",
            "s3://stelar-spatiotemporal/fields_test.gpkg",
            "s3://stelar-spatiotemporal/resunet-a_avg_2023-03-25-21-24-38",
            "-sdates",
            "2020-07-04,2020-07-07",
        ]

        os.environ["MINIO_ACCESS_KEY"] = "minioadmin"
        os.environ["MINIO_SECRET_KEY"] = "minioadmin"
        os.environ["MINIO_ENDPOINT_URL"] = "http://localhost:9000"

    args_dict = parse_args(args)
    segmentation_pipeline(**args_dict)