#!/bin/bash

docker pull alexdarancio7/stelar_image2ts:latest

MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_ENDPOINT_URL=http://localhost:9000

ras_paths="s3://stelar-spatiotemporal/LAI/30TYQ_LAI_2020.RAS"
rhd_paths="s3://stelar-spatiotemporal/LAI/30TYQ_LAI_2020.RHD"
out_dir="s3://stelar-spatiotemporal/LAI"
fields_path="s3://stelar-spatiotemporal/fields.gpkg"

docker run -it \
-e MINIO_ACCESS_KEY=$MINIO_ACCESS_KEY \
-e MINIO_SECRET_KEY=$MINIO_SECRET_KEY \
-e MINIO_ENDPOINT_URL=$MINIO_ENDPOINT_URL \
--network="host" \
alexdarancio7/stelar_image2ts \
$ras_paths $rhd_paths $out_dir $fields_path -skipfields
