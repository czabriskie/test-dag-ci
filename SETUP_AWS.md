# AWS Setup Guide for CI/CD Pipeline

This document outlines the AWS resources and configurations required to support the GitHub Actions CI/CD pipeline for deploying Airflow DAGs and Helm charts.

## 1. IAM Permissions

Create an IAM User (or an IAM Role if using OIDC) for GitHub Actions with the following permissions.

### Policy Example
Create a new policy (e.g., `GitHubActionsDAGsDeployPolicy`) with the following JSON:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "S3ArtifactsAccess",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::<YOUR_S3_BUCKET_NAME>",
                "arn:aws:s3:::<YOUR_S3_BUCKET_NAME>/*"
            ]
        },
        {
            "Sid": "S3HelmRepoAccess",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::<YOUR_HELM_S3_BUCKET>",
                "arn:aws:s3:::<YOUR_HELM_S3_BUCKET>/*"
            ]
        }
    ]
}
```
*Note: Replace `<YOUR_S3_BUCKET_NAME>` with your deployment artifacts bucket name and `<YOUR_HELM_S3_BUCKET>` with your Helm chart repository bucket name. If they're the same bucket, you can combine them into one statement.*

## 2. S3 Bucket for Deployment Artifacts

Create an S3 bucket to store deployment artifacts (DAGs, Helm charts, configurations).

*   **Bucket Name**: Unique name (e.g., `zontal-dags-artifacts`).
*   **Region**: Same as your other resources (e.g., `us-east-1`).
*   **Settings**: Block all public access.

## 3. GitHub Secrets Configuration

Navigate to your GitHub Repository -> **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**.

Add the following secrets:

### Required Secrets

| Secret Name             | Description                                       | Example Value                              |
| :---------------------- | :------------------------------------------------ | :----------------------------------------- |
| `AWS_ACCESS_KEY_ID`     | Access Key ID for the IAM User created in Step 1. | `AKIAIOSFODNN7EXAMPLE`                     |
| `AWS_SECRET_ACCESS_KEY` | Secret Access Key for the IAM User.               | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_REGION`            | The AWS Region where resources are created.       | `us-east-1`                                |
| `S3_BUCKET_NAME`        | The name of the S3 bucket created in Step 2.      | `zontal-dags-artifacts`                    |
| `HELM_S3_REPO`          | S3 URI for Helm chart repository (if using S3).   | `s3://your-bucket/your-path/chart-repo/`   |

**Note**: `HELM_S3_REPO` is only required if your Helm chart dependencies use an S3-based repository.

### GitHub Variables (optional)

Navigate to your GitHub Repository -> **Settings** -> **Secrets and variables** -> **Actions** -> **Variables** tab.

| Variable Name               | Description                                              | Default Value | Example Value |
| :-------------------------- | :------------------------------------------------------- | :------------ | :------------ |
| `UPDATE_CHART_DEPENDENCIES` | Whether to update Helm chart dependencies automatically. | `false`       | `true`        |

**Note**: `UPDATE_CHART_DEPENDENCIES` should be set to `true` only if there is no `Chart.lock` file or you want to force update dependencies.

## 4. CI/CD Workflow Overview

The GitHub Actions workflow deploys Airflow DAGs and Helm charts to S3:

### deploy-dags Job

The deployment process:
1. **Remove old artifacts**: Clears previous deployment artifacts from S3
2. **Install Helm**: Installs Helm and the Helm S3 plugin for S3-based chart repositories
3. **Package Helm charts**:
   - Updates chart versions with branch/tag name
   - Builds chart dependencies (using Chart.lock)
   - Packages charts as `.tgz` files
   - Zips configuration directories if present
4. **Package DAGs**:
   - Packages Airflow resources (connections, drivers, plugins, pools, variables)
   - Packages DAG files from `src/` directory
   - Includes license files and BOM
5. **Upload to S3**: Uploads all artifacts to S3

### Artifact Structure

All artifacts are uploaded to: `s3://{S3_BUCKET_NAME}/zontal/{repo-name}/{branch-or-tag}/`

Contents in `staging/`:
- `{repo-name}-{branch}.zip`: DAGs and Airflow configurations
- `{chart-name}-{version}.tgz`: Packaged Helm charts
- `configurations.zip`: Chart configurations (if present)
- `bom.yml`: Bill of materials
- `LICENSE*`: License files

## 5. Helm Chart Dependencies

This project uses Helm charts with dependencies. The workflow:
- Installs the Helm S3 plugin to support S3-based Helm repositories
- Requires `Chart.lock` file for reproducible builds
- Can force dependency updates by setting `UPDATE_CHART_DEPENDENCIES=true`
- Dependencies will be built from the repositories specified in your `Chart.yaml`

Ensure your `charts/*/Chart.yaml` files reference dependencies correctly. You can use S3, HTTPS, or other supported repository types:
```yaml
dependencies:
  - name: dag-charts
    repository: "s3://your-bucket/your-path/chart-repo/"
    version: ^1.0
```

Or HTTPS:
```yaml
dependencies:
  - name: dag-charts
    repository: "https://your-helm-repo.example.com"
    version: ^1.0
```
