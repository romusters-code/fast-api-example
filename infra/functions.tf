# resource "azurerm_service_plan" "sp20embedding001" {
#   name                = "embedding-fa-sp"
#   resource_group_name = azurerm_resource_group.rg20embedding001.name
#   location            = azurerm_resource_group.rg20embedding001.location
#   os_type             = "Linux"
#   sku_name            = "B1"       # B1 is a basic SKU; change if necessary
# }
#
# resource "azurerm_linux_function_app" "fa20embedding001" {
#   name                = "embedding-fa"
#   resource_group_name = azurerm_resource_group.rg20embedding001.name
#   location            = azurerm_resource_group.rg20embedding001.location
#
#   storage_account_name       = azurerm_storage_account.sa20faembedding001.name
#   storage_account_access_key = azurerm_storage_account.sa20faembedding001.primary_access_key
#   service_plan_id            = azurerm_service_plan.sp20embedding001.id
#   # https_only                 = true
#
#   # identity {
#   #   type = "SystemAssigned"
#   # }
#
#   # app_settings = {
#   #   FUNCTIONS_WORKER_RUNTIME            = "python"
#   #   FUNCTION_APP_EDIT_MODE              = "readOnly"
#   #   DOCKER_REGISTRY_SERVER_USERNAME     = azurerm_container_registry.acr.admin_username
#   #   DOCKER_REGISTRY_SERVER_URL          = azurerm_container_registry.acr.login_server
#   #   DOCKER_REGISTRY_SERVER_PASSWORD     = azurerm_container_registry.acr.admin_password
#   #   WEBSITES_ENABLE_APP_SERVICE_STORAGE = false
#   # }
#
#   site_config {
#     application_stack {
#       docker {
#         image_name   = "embedding_service"
#         image_tag    = "latest"
#         registry_url = azurerm_container_registry.acr.login_server
#       }
#     }
#     # always_on     = false
#     # http2_enabled = true
#     # ftps_state    = "Disabled"
#   }
# }



resource "azurerm_log_analytics_workspace" "la20embedding001" {
  name                = "la20embedding001"
  location            = azurerm_resource_group.rg20embedding001.location
  resource_group_name = azurerm_resource_group.rg20embedding001.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_container_app_environment" "cae20embedding001" {
  name                       = "cae20embedding001"
  location                   = azurerm_resource_group.rg20embedding001.location
  resource_group_name        = azurerm_resource_group.rg20embedding001.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.la20embedding001.id
}

resource "azurerm_container_app" "ca20embedding001" {
  name                         = "ca20embedding001"
  container_app_environment_id = azurerm_container_app_environment.cae20embedding001.id
  resource_group_name          = azurerm_resource_group.rg20embedding001.name
  revision_mode                = "Single"

  registry {
    server               = azurerm_container_registry.acr.login_server
    username             = azurerm_container_registry.acr.admin_username
    password_secret_name = "docker-io-pass"

  }

  ingress {
    allow_insecure_connections = false
    external_enabled           = true
    target_port                = 80
    traffic_weight {
      latest_revision = true
      percentage = 100
    }

  }
  template {
    container {
      name   = "embedding-service-container-app"
      image  = "EmbeddingContainerRegistry/embedding_service:latest"
      cpu    = 0.25
      memory = "0.5Gi"
    }
  }
  secret {
    name  = "docker-io-pass"
    value = azurerm_container_registry.acr.admin_password
  }
}

