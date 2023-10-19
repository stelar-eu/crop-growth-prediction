#!/bin/bash

docker login

docker build -t alexdarancio7/stelar_image2ts:latest .

docker push alexdarancio7/stelar_image2ts:latest