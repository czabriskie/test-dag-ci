#!/bin/bash
set -e

VERSION="${REF_NAME}"
REPO_PATH="${REPO_NAME}"

S3_DIR="zontal/${REPO_PATH}/${VERSION}"

# copy staging artifacts to s3
test -d ./staging && ls -lh staging
test -d ./staging && echo "Copying artifacts to ${S3_BUCKET}/${S3_DIR}"
test -d ./staging && aws s3 cp --region "${S3_REGION}" --no-progress --storage-class INTELLIGENT_TIERING --recursive "staging" "s3://${S3_BUCKET}/${S3_DIR}"

# Find all files ending with bom.yml in the current directory
bom_files=$(find . -name "*bom.yml" -type f)

if [ -n "$bom_files" ]; then
    # Copy all found bom.yml files
    echo "$bom_files" | while read -r bom_file; do
        aws s3 cp --region "${S3_REGION}" --no-progress --storage-class INTELLIGENT_TIERING "$bom_file" "s3://${S3_BUCKET}/${S3_DIR}/"
    done
else
    # No bom.yml files found, create default one
    echo "# ${S3_DIR}" > bom.yml
    aws s3 cp --region "${S3_REGION}" --no-progress --storage-class INTELLIGENT_TIERING "bom.yml" "s3://${S3_BUCKET}/${S3_DIR}/"
fi
