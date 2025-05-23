# Optional Config - Fusion Binary Vendoring
Wave-Lite allows you to augment your container manifests in flight. For example, pre-existing containers requiring Seqera's Fusion binary will undergo the following process:

1. Container manifest is retrieved from the source registry by Wave-Lite.
2. Wave-Lite adds an additional manifest layer which points to a storage location where the Fusion binary can be found.
3. The augmented manifest is returned to the compute node for blob retrieval and container creation.

By default, the injected Fusion storage location points to a Seqera-managed Content Delivery Network (CDN): `https://fusionfs.seqera.io/`.


## Considerations 
The default implemenation offers pros and cons:

#### Pros
- You externalize hosting & distribution responsibilities to Seqera.
- You avoid additional pipeline configuration requirements within your Seqera Platform instance.
- You (potentially) avoid extra object storage permissions granted to your compute nodes.
- You do not need to follow upstream Seqera development work as closely (_i.e. Fusion patch releases_).

#### Cons
- You retain an external dependency to a Seqera-managed asset.
- An additional egress route must be whitelisted.


## Vendoring Steps
Many Fusion clients choose to stay with the default implementation. However, for those who wish more control over this facet of their implementation, the following steps provide guidance on how to vendor your own Fusion binary instance. 

**NOTE:** 

1. These steps assume you will store the binary in an S3 bucket. Other file server options are possible but will not be covered.
2. Steps use Fusion v2.5 as an example. Please update to your desired version, as required.


### Prerequisites

- AWS CLI configured with appropriate permissions
- Access to the target S3 bucket
- `curl` or `wget` installed

### Steps

#### 1. Download Required Files

Download both the configuration JSON and the container archive:

```bash
# Download the config file
curl -O https://fusionfs.seqera.io/releases/v2.5-amd64.json

# Download the container archive
curl -O https://fusionfs.seqera.io/releases/pkg/2/5/0/fusion-amd64.tar.gz
```

#### 2. Upload Files to S3

Upload both files to your private S3 bucket:

```bash
# Upload the config file
aws s3 cp v2.5-amd64.json s3://your-bucket/fusion/v2.5-amd64.json

# Upload the container archive
aws s3 cp fusion-amd64.tar.gz s3://your-bucket/fusion/pkg/2/5/0/fusion-amd64.tar.gz
```

#### 3. Update Configuration

Modify the `v2.5-amd64.json` file to point to your S3 bucket. Replace the `location` field with your S3 URL:

```json
{
  "entrypoint": ["/usr/bin/fusion"],
  "env": [
    "FUSION_CONFIG_PROFILE=nextflow",
    "FUSION_COMPACT_SYMLINKS=true",
    "FUSION_SHOW_GLOBAL_INFO=true"
  ],
  "layers": [
    {
      "location": "https://your-bucket.s3.region.amazonaws.com/fusion/pkg/2/5/0/fusion-amd64.tar.gz",
      "gzipDigest": "sha256:47d8862d0a27838a888a65265c081a21eb30052e2914baeaed5ea301a04a6b85",
      "gzipSize": 36067881,
      "tarDigest": "sha256:c4ac9c2aa25febb441f1a0e5161eaeb774f9c1a3f52c1a6564694f17fd978acc",
      "skipHashing": true
    }
  ]
}
```

#### 4. Configure Nextflow

Update your Nextflow configuration to use the mirrored files:

```groovy
fusion.containerConfigUrl = 'https://your-bucket.s3.region.amazonaws.com/fusion/v2.5-amd64.json'
```

### Verification

To verify the setup:

1. Ensure both files are accessible in your S3 bucket
2. Verify the JSON file contains the correct S3 URL in the `location` field
3. Test a Nextflow pipeline that uses Fusion containers

### Troubleshooting

Common issues and solutions:

- If access is denied:
    - Check VPC endpoint and bucket policies
    - Check Compute Environment IAM permissions
- Verify HTTPS is being used for all S3 URLs
- Ensure the gzipDigest and tarDigest values match the original file

### File Structure

Your S3 bucket should have this structure:

```
your-bucket/
├── fusion/
│   ├── v2.5-amd64.json
│   └── pkg/
│       └── 2/
│           └── 5/
│               └── 0/
│                   └── fusion-amd64.tar.gz
```
