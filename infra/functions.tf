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
    target_port                = 81
    traffic_weight {
      latest_revision = true
      percentage = 100
    }

  }
  template {
    container {
      name   = "embedding-service-container-app"
      image  = "${azurerm_container_registry.acr.login_server}/embedding_service:latest"
      cpu    = 0.25
      memory = "0.5Gi"
    }
  }
  secret {
    name  = "docker-io-pass"
    value = azurerm_container_registry.acr.admin_password
  }
}

