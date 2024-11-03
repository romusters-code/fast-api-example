# We strongly recommend using the required_providers block to set the
# Azure Provider source and version being used
terraform {
  required_version = "~>1.9.8"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "4.8.0"
    }
  }
}

# Configure the Microsoft Azure Provider
provider "azurerm" {
  features {}
  subscription_id = "8cdc4695-331d-4883-97e0-2184f3577822"
}

data "azurerm_client_config" "current" {
}
# Create a resource group
resource "azurerm_resource_group" "rg20embedding001" {
  name     = "rg20embedding001"
  location = "North Europe"
}
