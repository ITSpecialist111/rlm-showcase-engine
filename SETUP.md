# RLM Showcase Engine - Setup Guide

## Overview

The Recursive Language Model (RLM) Showcase Engine is a production-ready implementation of hierarchical language model architecture designed for Microsoft Foundry. It supports processing documents with 10M+ token contexts through intelligent chunking and multi-agent orchestration.

## Prerequisites

- Python 3.9+
- - Subscription with Microsoft Foundry access
  - - Git
    - - Docker (optional, for containerized deployment)
     
      - ## Quick Start - Local Development
     
      - ### 1. Clone and Setup
     
      - ```bash
        git clone https://github.com/ITSpecialist111/rlm-showcase-engine.git
        cd rlm-showcase-engine

        # Create virtual environment
        python -m venv venv

        # Activate virtual environment
        # On macOS/Linux:
        source venv/bin/activate
        # On Windows:
        venv\Scripts\activate

        # Install dependencies
        pip install -r requirements.txt
        ```

        ### 2. Configuration (Azure Functions Local)

        Create `local.settings.json` in the root (do not commit this file):

        ```json
        {
          "IsEncrypted": false,
          "Values": {
            "AzureWebJobsStorage": "", 
            "FUNCTIONS_WORKER_RUNTIME": "python",
            "FOUNDRY_ENDPOINT": "https://your-resource.openai.azure.com/",
            "FOUNDRY_API_KEY": "your-key",
            "ROOT_AGENT_DEPLOYMENT": "gpt-5.1-chat",
            "WORKSPACE_ROOT": "."
          }
        }
        ```
        *Note: `AzureWebJobsStorage` is left empty to run without local storage emulator for lightweight testing.*

        ### 3. Test the Engine

        **Run the Host:**
        ```bash
        func host start -p 7072
        ```

        **Run the Verification Script:**
        ```bash
        python tests/check_repl.py
        ```

        ```python
        import asyncio
        from rlm_engine import RLMEngine, RLMConfig
        from context_manager import ContextManager
        import os

        # Initialize engine
        config = RLMConfig(
            foundry_endpoint=os.getenv("FOUNDRY_ENDPOINT"),
            api_key=os.getenv("FOUNDRY_API_KEY")
        )

        engine = RLMEngine(config)

        # Process query
        async def test():
            documents = [
                "Document 1 content here...",
                "Document 2 content here..."
            ]

            response = await engine.process_query(
                "Analyze the key insights from these documents",
                documents=documents
            )

            print(f"Status: {response.status}")
            print(f"Result: {response.result}")
            print(f"Reasoning Steps: {response.reasoning_steps}")

        asyncio.run(test())
        ```

        ## Azure Deployment

        ### 1. Create Azure Resources

        ```bash
        # Create resource group
        az group create \
          --name rg-rlm-showcase-uksouth \
          --location uksouth

        # Create storage account for document storage
        az storage account create \
          --name rlmdocumentsstorage \
          --resource-group rg-rlm-showcase-uksouth \
          --location uksouth \
          --sku Standard_LRS
        ```

        ### 2. Deploy Function App

        ```bash
        # Create function app
        az functionapp create \
          --name rlm-engine-uksouth \
          --storage-account rlmdocumentsstorage \
          --resource-group rg-rlm-showcase-uksouth \
          --runtime python \
          --runtime-version 3.11 \
          --functions-version 4

        # Deploy code
        func azure functionapp publish rlm-engine-uksouth
        ```

        ### 3. Configure Function App Settings

        ```bash
        # Set environment variables
        az functionapp config appsettings set \
          --name rlm-engine-uksouth \
          --resource-group rg-rlm-showcase-uksouth \
          --settings \
          FOUNDRY_ENDPOINT="your-endpoint" \
          FOUNDRY_API_KEY="your-key" \
          AZURE_SUBSCRIPTION_ID="your-sub-id"
        ```

        ## Docker Deployment

        ### Build and Run Locally

        ```bash
        # Build Docker image
        docker build -t rlm-engine:latest -f docker/Dockerfile .

        # Run container
        docker run -p 8000:7071 \
          -e FOUNDRY_ENDPOINT="your-endpoint" \
          -e FOUNDRY_API_KEY="your-key" \
          rlm-engine:latest
        ```

        ### Docker Compose (with supporting services)

        ```bash
        cd docker
        docker-compose up
        ```

        ## API Endpoints

        ### Health Check
        ```
        GET /api/health

        Response:
        {
          "status": "healthy",
          "version": "1.0.0",
          "timestamp": "2026-01-18T11:04:49Z"
        }
        ```

        ### Process Query
        ```
        POST /api/query

        Request:
        {
          "query": "Analyze the documents",
          "documents": ["doc1 content", "doc2 content"],
          "max_iterations": 10
        }

        Response:
        {
          "status": "completed",
          "result": "Analysis results here",
          "reasoning_steps": ["Step 1", "Step 2"],
          "iterations_used": 3
        }
        ```

        ## Testing

        ### Run Unit Tests

        ```bash
        pytest tests/test_rlm_engine.py -v
        ```

        ### Run Benchmarks

        ```bash
        python tests/benchmark_rlm.py
        ```

        ### Run Integration Tests

        ```bash
        pytest tests/integration_test.py -v
        ```

        ## Copilot Studio Integration

        ### 1. Create Webhook Endpoint

        In Copilot Studio:
        - Create new plugin
        - - Configure webhook URL: `https://rlm-engine-uksouth.azurewebsites.net/api/copilot-webhook`
          - - Set authentication with Function Key
           
            - ### 2. Create Bot Topics
           
            - Example topic for document analysis:
            - - Trigger: "Analyze documents for me"
              - - Action: Call RLM Engine webhook
                - - Show results in response
                 
                  - ### 3. Test in Copilot
                 
                  - 1. Upload test documents
                    2. 2. Ask questions about document content
                       3. 3. Engine decomposes query, processes with sub-agents, synthesizes results
                         
                          4. ## Monitoring and Logging
                         
                          5. ### Application Insights
                         
                          6. All operations are logged to Application Insights:
                         
                          7. ```python
                             from monitoring.app_insights import AppInsights

                             insights = AppInsights()
                             insights.log_event("query_processed", {
                                 "query": "example",
                                 "status": "success",
                                 "duration_ms": 1234
                             })
                             ```

                             ### View Logs

                             ```bash
                             # In Azure portal
                             az monitor app-insights metrics list \
                               --resource-group rg-rlm-showcase-uksouth \
                               --app rlm-app-insights
                             ```

                             ## Troubleshooting

                             ### Authentication Errors

                             ```
                             Error: Authentication failed for Foundry endpoint
                             Solution:
                             1. Verify FOUNDRY_API_KEY is correct
                             2. Check FOUNDRY_ENDPOINT format
                             3. Ensure API key has proper permissions
                             ```

                             ### Timeout Errors

                             ```
                             Error: Query processing exceeded max iterations
                             Solution:
                             1. Increase MAX_ITERATIONS in config
                             2. Reduce document size with chunking
                             3. Simplify query complexity
                             ```

                             ### Memory Issues

                             ```
                             Error: Out of memory during document processing
                             Solution:
                             1. Reduce chunk_size in ContextManager
                             2. Reduce max_context_tokens
                             3. Process documents in batches
                             ```

                             ## Performance Tips

                             1. **Document Chunking**: Optimize chunk_size based on your documents
                             2. 2. **Parallel Processing**: Sub-agents run in parallel for faster execution
                                3. 3. **Context Optimization**: Only relevant chunks are selected
                                   4. 4. **Async Operations**: All API calls are async for better performance
                                     
                                      5. ## Production Checklist
                                     
                                      6. - [ ] Configure proper error handling
                                         - [ ] - [ ] Set up monitoring and alerting
                                         - [ ] - [ ] Configure auto-scaling for Function App
                                         - [ ] - [ ] Set up CI/CD pipeline
                                         - [ ] - [ ] Test disaster recovery
                                         - [ ] - [ ] Document custom configurations
                                         - [ ] - [ ] Set up backup for documents
                                         - [ ] - [ ] Configure rate limiting
                                        
                                         - [ ] ## Support
                                        
                                         - [ ] For issues or questions:
                                         - [ ] 1. Check the troubleshooting section
                                         - [ ] 2. Review logs in Application Insights
                                         - [ ] 3. Create issue in GitHub repository
                                         - [ ] 4. Contact the development team
                                        
                                         - [ ] ## License
                                        
                                         - [ ] MIT License - See LICENSE file for details
                                        
                                         - [ ] ## Changelog
                                        
                                         - [ ] ### Version 1.0.0 (2026-01-18)
                                         - [ ] - Initial release
                                         - [ ] - Core RLM engine implementation
                                         - [ ] - Hierarchical agent support
                                         - [ ] - Microsoft Foundry integration
                                         - [ ] - 10M+ token context support
