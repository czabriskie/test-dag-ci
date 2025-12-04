#!/bin/bash
set -e

VERSION="${REF_NAME}"
REPO_PATH="${REPO_NAME}"

# remove staging artifacts from s3
S3_DIR="zontal/${REPO_PATH}/${VERSION}"

echo "Removing artifacts from ${S3_BUCKET}/${S3_DIR}"
aws s3 rm --region ${S3_REGION} --recursive "s3://${S3_BUCKET}/${S3_DIR}"
