// Azure configuration and workload-identity foundation.
// This file is declarative only: build/validate it locally before any approved deployment.
targetScope = 'resourceGroup'

@description('Azure region for the isolated environment foundation.')
param location string = resourceGroup().location

@allowed([
  'staging'
  'production'
])
@description('Cloud environment. Local emulators are intentionally not represented here.')
param environment string

@minLength(3)
@maxLength(18)
@description('Globally unique, lowercase resource-name prefix supplied by the deployment owner.')
param namePrefix string

var identityName = '${namePrefix}-${environment}-workload'
var appConfigName = '${namePrefix}-${environment}-config'
var vaultName = '${namePrefix}-${environment}-kv'

resource workloadIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
}

resource appConfiguration 'Microsoft.AppConfiguration/configurationStores@2023-03-01' = {
  name: appConfigName
  location: location
  sku: {
    name: 'standard'
  }
  properties: {
    publicNetworkAccess: 'Disabled'
    disableLocalAuth: true
  }
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: vaultName
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    enablePurgeProtection: true
    publicNetworkAccess: 'Disabled'
  }
}

// App Configuration Data Reader. Assignments are scoped to the workload identity.
resource appConfigReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(appConfiguration.id, identityName, 'AppConfigurationDataReader')
  scope: appConfiguration
  properties: {
    principalId: workloadIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '516239f1-63e1-4d78-a4de-a74fb236a071'
    )
  }
}

// Key Vault Secrets User. Keep only secrets that cannot be eliminated by Entra ID.
resource keyVaultSecretsUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, identityName, 'KeyVaultSecretsUser')
  scope: keyVault
  properties: {
    principalId: workloadIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '4633458b-17de-408a-b874-0445c86b69ea'
    )
  }
}

output workloadIdentityClientId string = workloadIdentity.properties.clientId
output appConfigurationEndpoint string = appConfiguration.properties.endpoint
output keyVaultUri string = keyVault.properties.vaultUri
