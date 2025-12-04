#!/bin/bash
set -e

if [ -d "charts" ]; then
  for chart in charts/*; do
    echo "📝 Updating appVersion for chart: $chart"
    sed -i.bak 's/^appVersion:.*/appVersion: '"${REF_NAME}"'/' "$chart"/Chart.yaml
    rm -f "$chart"/Chart.yaml.bak

    # If there exists a configurations directory, zip and add to staging
    config_dir="$chart/configurations"
    if [ -d "$config_dir" ]; then
        echo "🗜️  Zipping configurations directory for chart: $chart"
        zip_file="${chart}/configurations.zip"
        (cd "$chart" && zip -r "$(basename "$zip_file")" "configurations")
        mv "$zip_file" staging/
    else
      echo "⚠️  No configurations directory found for chart: $chart"
    fi

    # Package Chart
    if [ -f "$chart/Chart.lock" ]; then
        echo "🔒 Using existing lockfile for dependencies in: $chart"
        helm dependency build "$chart"
    elif [ "$UPDATE_CHART_DEPENDENCIES" = "true" ]; then
        echo "⚙️  No lockfile found, but UPDATE_CHART_DEPENDENCIES override set to 'true'. Updating dependencies for: $chart"
        helm dependency update "$chart"
    else
        echo "❌ ERROR: No lockfile found for Helm dependencies. To override, set 'UPDATE_CHART_DEPENDENCIES=true' in the CICD variables."
        exit 1
    fi

    echo "📦 Packaging chart: $chart"
    helm package "$chart" -d ./staging

  done
else
  echo "❓ No charts directory found."
fi
