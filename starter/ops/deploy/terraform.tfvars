namespace       = "citetrace"
release_tag     = "1.0.0"
cluster_name    = "citetrace-prod"
region          = "us-east-1"
container_registry = "ghcr.io/citetrace"

api_min_replicas   = 3
api_max_replicas   = 12
worker_min_replicas = 4
worker_max_replicas = 20
web_min_replicas   = 3
web_max_replicas   = 10

database_instance_class = "db.r7g.4xlarge"
database_storage_gb     = 1000
database_multi_az       = true
database_backup_window  = "03:00-04:00"

redis_node_type   = "cache.r7g.2xlarge"
redis_num_shards  = 3
redis_multi_az    = true

grobid_min_replicas = 2
grobid_max_replicas = 8
grobid_cpu_per_pod  = "4"
grobid_memory_per_pod = "8Gi"

otel_collector_endpoint = "https://otel-collector.internal:4317"
log_retention_days      = 30
metrics_retention_days  = 365

secret_rotation_check_days = 30
