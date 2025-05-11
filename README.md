# 1. Build the Docker image.
```bash
docker build -t validation-service .
```
# 2. Run the container
```bash
docker run -v $(pwd)/src/validation_service:/app/src/validation_service validation-service  
```
