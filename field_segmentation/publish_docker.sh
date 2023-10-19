#!/bin/bash

docker login

docker build -t alexdarancio7/stelar_field_segmentation:latest .

docker push alexdarancio7/stelar_field_segmentation:latest