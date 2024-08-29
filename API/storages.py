from storages.backends.s3boto3 import S3Boto3Storage


class TINETUserFilesStorage(S3Boto3Storage):
    bucket_name = 'tinetuserfiles'
