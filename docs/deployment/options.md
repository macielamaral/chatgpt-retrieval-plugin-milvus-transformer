
# You can check the original plugin information:
https://github.com/openai/chatgpt-retrieval-plugin

# Deployment Options:

Some possible options for deploying the app are:

- **Flyio**
- **Heroku**
- **Render**
- **Azure Container Apps**
- **Google Cloud Run**: 
- **AWS Elastic Container Service**:

## Removing Unused Dependencies

Before deploying your app, you might want to remove unused dependencies from your [pyproject.toml](/pyproject.toml) file to reduce the size of your app and improve its performance. Depending on the vector database provider you choose, you can remove the packages that are not needed for your specific provider.

