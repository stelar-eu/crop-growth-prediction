#!/bin/bash

docker pull alexdarancio7/stelar_field_segmentation:latest

export MINIO_ACCESS_KEY="minioadmin"
export MINIO_SECRET_KEY="minioadmin"
export MINIO_ENDPOINT_URL="http://localhost:9000"

b2_path="s3://stelar-spatiotemporal/RGB/B2"
b3_path="s3://stelar-spatiotemporal/RGB/B2"
b4_path="s3://stelar-spatiotemporal/RGB/B2"
b8_path="s3://stelar-spatiotemporal/RGB/B2"
out_path="s3://stelar-spatiotemporal/fields_test.gpkg"
model_path="s3://stelar-spatiotemporal/resunet-a_avg_2023-03-25-21-24-38"
sdates="2020-07-04,2020-07-07"

python3 segmentation_pipeline.py $b2_path $b3_path $b4_path $b8_path $out_path $model_path -sdates $sdates
