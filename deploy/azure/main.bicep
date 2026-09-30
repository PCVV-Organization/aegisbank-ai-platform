// Azure configuration, workload-identity, and Container Apps staging foundation.
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

@description('Container image reference for Agent API.')
param agentImage string = 'mcr.microsoft.com/azuredocs/aci-helloworld:latest'

@description('Container image reference for Mock Core Banking.')
param coreBankingImage string = 'mcr.microsoft.com/azuredocs/aci-helloworld:latest'

var identityName = '${namePrefix}-${environment}-workload'
var appConfigName = '${namePrefix}-${environment}-config'
var vaultName = '${namePrefix}-${environment}-kv'
var logWorkspaceName = '${namePrefix}-${environment}-logs'
var containerEnvName = '${namePrefix}-${environment}-aca-env'
var serviceBusName = '${namePrefix}-${environment}-sb'
var queueName = 'aegisbank-events'

resource workloadIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
}

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logWorkspaceName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
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

resource serviceBus 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' = {
  name: serviceBusName
  location: location
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
  properties: {
    disableLocalAuth: true
    minimumTlsVersion: '1.2'
  }
}

resource serviceBusQueue 'Microsoft.ServiceBus/namespaces/queues@2022-10-01-preview' = {
  parent: serviceBus
  name: queueName
  properties: {
    lockDuration: 'PT1M'
    maxDeliveryCount: 10
    deadLetteringOnMessageExpiration: true
  }
}

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: containerEnvName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource mockCoreBankingApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: '${namePrefix}-${environment}-core-banking'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${workloadIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      ingress: {
        external: false
        targetPort: 8000
        transport: 'auto'
      }
    }
    template: {
      containers: [
        {
          name: 'mock-core-banking'
          image: coreBankingImage
          resources: {
            cpu: json('0.5')
            memory: '1.0Gi'
          }
          env: [
            {
              name: 'AEGISBANK_ENV'
              value: environment
            }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health/live'
                port: 8000
              }
              periodSeconds: 15
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/health/ready'
                port: 8000
              }
              periodSeconds: 15
            }
          ]
        }
      ]
    }
  }
}

resource agentApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: '${namePrefix}-${environment}-agent'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${workloadIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
    }
    template: {
      containers: [
        {
          name: 'aegisbank-agent'
          image: agentImage
          resources: {
            cpu: json('0.5')
            memory: '1.0Gi'
          }
          env: [
            {
              name: 'AEGISBANK_ENV'
              value: environment
            }
            {
              name: 'AZURE_CLIENT_ID'
              value: workloadIdentity.properties.clientId
            }
            {
              name: 'AZURE_APPCONFIG_ENDPOINT'
              value: appConfiguration.properties.endpoint
            }
            {
              name: 'MOCK_CORE_BANKING_BASE_URL'
              value: 'http://${mockCoreBankingApp.name}'
            }
            {
              name: 'AEGISBANK_SERVICEBUS_FQDN'
              value: '${serviceBus.name}.servicebus.windows.net'
            }
            {
              name: 'AEGISBANK_SERVICEBUS_QUEUE'
              value: queueName
            }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health/live'
                port: 8000
              }
              periodSeconds: 15
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/health/ready'
                port: 8000
              }
              periodSeconds: 15
            }
          ]
        }
      ]
    }
  }
}

// App Configuration Data Reader
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

// Key Vault Secrets User
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

// Azure Service Bus Data Sender
resource serviceBusDataSender 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(serviceBus.id, identityName, 'AzureServiceBusDataSender')
  scope: serviceBus
  properties: {
    principalId: workloadIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '69a216fc-b8fb-44d8-bc22-1f3c2cd27a39'
    )
  }
}

// Azure Service Bus Data Receiver
resource serviceBusDataReceiver 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(serviceBus.id, identityName, 'AzureServiceBusDataReceiver')
  scope: serviceBus
  properties: {
    principalId: workloadIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '4f6d3a01-5356-424a-9274-02e06e644125'
    )
  }
}

output workloadIdentityClientId string = workloadIdentity.properties.clientId
output appConfigurationEndpoint string = appConfiguration.properties.endpoint
output keyVaultUri string = keyVault.properties.vaultUri
output serviceBusEndpoint string = '${serviceBus.name}.servicebus.windows.net'
output agentFqdn string = agentApp.properties.configuration.ingress.fqdn
