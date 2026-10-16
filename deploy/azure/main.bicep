// Azure configuration, workload-identity, and Container Apps staging foundation.
// This file is declarative only: build/validate it locally before any approved deployment.
targetScope = 'resourceGroup'

@description('Azure region for the isolated environment foundation.')
param location string = resourceGroup().location

@description('Azure region for the user-assigned workload identity. Must satisfy subscription region policy.')
param identityLocation string = 'westus2'

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
param agentImage string

@description('Container image reference for Mock Core Banking.')
param coreBankingImage string

@description('Existing Azure Container Registry name used by staging Container Apps.')
param registryName string = 'aegisbankstagingacr'

@description('Existing user-assigned identity used by staging workloads.')
param workloadIdentityName string = 'id-aegisbank-staging-workload'

@description('Existing Azure AI Services account used for cloud model inference.')
param foundryAccountName string = '${namePrefix}-${environment}-ai'

@description('Existing model deployment name in the Azure AI Services account.')
param foundryDeploymentName string = 'aegisbank-phi-4-mini'

@description('Stable role-assignment resource ID for the pre-authorized Foundry workload identity.')
param foundryRoleAssignmentName string = 'a32c0bf0-80e4-5c04-832b-fdc8553d5d43'

@description('Microsoft Entra tenant ID that issues access tokens for the Agent API. Empty keeps cloud authentication fail-closed.')
param entraTenantId string = ''

@description('Registered API audience accepted by the Agent API. Empty keeps cloud authentication fail-closed.')
param entraAudience string = ''

@description('JWT claim containing the synthetic AegisBank customer identifier.')
param entraCustomerIdClaim string = 'customer_id'

@description('Comma-separated HTTPS origins allowed to call the Agent API from browsers.')
param corsOrigins string = ''

@allowed([
  'entra'
  'synthetic-password'
])
@description('Explicit hosted authentication provider. Synthetic password is staging-laboratory only.')
param authMode string = 'entra'

@description('Pre-provisioned Cosmos DB database used by synthetic customer authentication.')
param authDatabaseName string = 'aegisbank-auth'

@description('Pre-provisioned Cosmos DB container used by synthetic customer authentication.')
param authContainerName string = 'identities'

@description('Opaque synthetic session lifetime in seconds.')
param authSessionTtlSeconds int = 900

@description('Existing Cosmos DB account used by staging authentication.')
param authCosmosAccountName string = 'aegisbankstagingcosmos'

@description('Maximum generated tokens per Foundry request to control Students quota consumption.')
param foundryMaxTokens int = 256

@description('Cosmos DB database used for durable synthetic chat history.')
param conversationDatabaseName string = 'aegisbank-chat'

@description('Cosmos DB container used for durable synthetic chat messages.')
param conversationContainerName string = 'messages'

@description('TTL for chat messages in seconds. Keeps staging storage bounded.')
param conversationTtlSeconds int = 2592000

var identityName = workloadIdentityName
var appConfigName = '${namePrefix}-${environment}-config'
var vaultName = '${namePrefix}-${environment}-kv'
var logWorkspaceName = '${namePrefix}-${environment}-logs'
var containerEnvName = '${namePrefix}-${environment}-aca-env'
var serviceBusName = '${namePrefix}-${environment}-bus'
var queueName = 'aegisbank-events'
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: registryName
}

resource conversationCosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' existing = {
  name: authCosmosAccountName
}

resource conversationDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  parent: conversationCosmosAccount
  name: conversationDatabaseName
  properties: {
    resource: {
      id: conversationDatabaseName
    }
  }
}

resource conversationContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: conversationDatabase
  name: conversationContainerName
  properties: {
    resource: {
      id: conversationContainerName
      partitionKey: {
        paths: [
          '/customer_id'
        ]
        kind: 'Hash'
      }
      defaultTtl: conversationTtlSeconds
    }
  }
}

resource conversationDataContributor 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-05-15' = {
  parent: conversationCosmosAccount
  name: guid(conversationCosmosAccount.id, identityName, 'conversation-data-contributor')
  properties: {
    principalId: workloadIdentity.properties.principalId
    roleDefinitionId: '${conversationCosmosAccount.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
    // Cosmos SDK requests database metadata before operating on a container.
    // Keep the assignment database-scoped (rather than account-scoped) so the
    // workload identity can resolve that metadata while retaining least
    // privilege for the conversation database.
    scope: '${conversationCosmosAccount.id}/dbs/${conversationDatabaseName}'
  }
}

resource workloadIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: identityLocation
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

// Microsoft Foundry Models resource. The model deployment is deliberately
// separate from Foundry Local and uses Entra ID rather than an API key.
resource foundryAccount 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: foundryAccountName
  location: location
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: foundryAccountName
    publicNetworkAccess: 'Enabled'
  }
}

resource foundryModelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: foundryAccount
  name: foundryDeploymentName
  sku: {
    name: 'GlobalStandard'
    capacity: 1
  }
  properties: {
    model: {
      format: 'Microsoft'
      name: 'Phi-4-mini-instruct'
      version: '1'
    }
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
      registries: [
        {
          server: containerRegistry.properties.loginServer
          identity: workloadIdentity.id
        }
      ]
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
  dependsOn: [
    containerRegistryPull
  ]
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
      registries: [
        {
          server: containerRegistry.properties.loginServer
          identity: workloadIdentity.id
        }
      ]
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
              value: 'http://${mockCoreBankingApp.properties.configuration.ingress.fqdn}'
            }
            {
              name: 'AEGISBANK_FOUNDRY_ENDPOINT'
              value: 'https://${foundryAccount.name}.cognitiveservices.azure.com/'
            }
            {
              name: 'AEGISBANK_FOUNDRY_DEPLOYMENT_NAME'
              value: foundryDeploymentName
            }
            {
              name: 'AEGISBANK_FOUNDRY_MAX_TOKENS'
              value: string(foundryMaxTokens)
            }
            {
              name: 'AEGISBANK_FOUNDRY_COMPACT_TOOLS'
              value: 'true'
            }
            {
              name: 'AEGISBANK_ENTRA_TENANT_ID'
              value: entraTenantId
            }
            {
              name: 'AEGISBANK_ENTRA_AUDIENCE'
              value: entraAudience
            }
            {
              name: 'AEGISBANK_ENTRA_CUSTOMER_ID_CLAIM'
              value: entraCustomerIdClaim
            }
            {
              name: 'AEGISBANK_CORS_ORIGINS'
              value: corsOrigins
            }
            {
              name: 'AEGISBANK_AUTH_MODE'
              value: authMode
            }
            {
              name: 'AEGISBANK_AUTH_COSMOS_ENDPOINT'
              value: 'https://${authCosmosAccountName}.documents.azure.com:443/'
            }
            {
              name: 'AEGISBANK_AUTH_COSMOS_DATABASE'
              value: authDatabaseName
            }
            {
              name: 'AEGISBANK_AUTH_COSMOS_CONTAINER'
              value: authContainerName
            }
            {
              name: 'AEGISBANK_AUTH_SESSION_TTL_SECONDS'
              value: string(authSessionTtlSeconds)
            }
            {
              name: 'CONVERSATION_COSMOS_DATABASE'
              value: conversationDatabaseName
            }
            {
              name: 'CONVERSATION_COSMOS_ENDPOINT'
              value: 'https://${authCosmosAccountName}.documents.azure.com:443/'
            }
            {
              name: 'CONVERSATION_COSMOS_CONTAINER'
              value: conversationContainerName
            }
            {
              name: 'CONVERSATION_PERSISTENCE_ENABLED'
              value: 'true'
            }
            {
              name: 'CONVERSATION_TTL_SECONDS'
              value: string(conversationTtlSeconds)
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
  dependsOn: [
    containerRegistryPull
    foundryModelDeployment
    foundryModelUser
  ]
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
      '4633458b-17de-408a-b874-0445c86b69e6'
    )
  }
}

// AcrPull
resource containerRegistryPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerRegistry.id, identityName, 'AcrPull')
  scope: containerRegistry
  properties: {
    principalId: workloadIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '7f951dda-4ed3-4680-a7ca-43fe172d538d'
    )
  }
}

// Allows the runtime identity to invoke the Foundry deployment with Entra ID.
resource foundryModelUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: foundryRoleAssignmentName
  scope: foundryAccount
  properties: {
    principalId: workloadIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
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

output workloadIdentityClientId string = workloadIdentity.properties.clientId
output appConfigurationEndpoint string = appConfiguration.properties.endpoint
output keyVaultUri string = keyVault.properties.vaultUri
output serviceBusEndpoint string = '${serviceBus.name}.servicebus.windows.net'
output agentFqdn string = agentApp.properties.configuration.ingress.fqdn
output foundryEndpoint string = 'https://${foundryAccount.name}.cognitiveservices.azure.com/'
output foundryDeploymentName string = foundryDeploymentName
