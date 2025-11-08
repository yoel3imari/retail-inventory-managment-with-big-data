from minio import Minio
from minio.error import S3Error

# Initialize MinIO client
client = Minio(
    "localhost:9000",  # MinIO server endpoint
    access_key="your-access-key",
    secret_key="your-secret-key",
    secure=False  # Set to True for HTTPS
)

# For MinIO Play (public test server)
client = Minio(
    "play.min.io",
    access_key="Q3AM3UQ867SPQQA43P2F",
    secret_key="zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG",
    secure=True
)