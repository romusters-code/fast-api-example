resource "azurerm_storage_account" "sa20faembedding001" {
  name                     = "sa20faembedding001"
  resource_group_name      = azurerm_resource_group.rg20embedding001.name
  location                 = azurerm_resource_group.rg20embedding001.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}
