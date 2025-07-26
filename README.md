All commands should be executed from validation-project folder.
# 1. Build the Docker image.
```bash
docker build -f build/Dockerfile -t validation-service .
```
# 2. Run the container
```bash
docker run -v $(pwd)/src:/app/src validation-service 
```
