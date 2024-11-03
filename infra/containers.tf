resource "azurerm_container_registry" "acr" {
  name                = "EmbeddingContainerRegistry"
  resource_group_name = azurerm_resource_group.rg20embedding001.name
  location            = azurerm_resource_group.rg20embedding001.location
  sku                 = "Basic"
  admin_enabled       = true
}
