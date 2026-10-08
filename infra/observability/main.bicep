// Observability for the Foundry agents: Log Analytics + workspace-based Application Insights,
// connected to a Foundry account and project (server-side agent tracing), with the Foundry
// resource's own logs and metrics sent to Log Analytics.
//
// Deploy only through the governed flow (plan, what-if, approval):
//   az deployment group what-if -g <rg> -f infra/observability/main.bicep -p foundryAccountName=<a> projectName=<p>
// Based on the official foundry-samples connection-application-insights.bicep, made
// workspace-based (classic Application Insights is retired). No identifiers are committed.

@description('Existing Foundry (AIServices) account name.')
param foundryAccountName string

@description('Existing Foundry project name (sub-resource of the account).')
param projectName string

@description('Region for Log Analytics and Application Insights (default: the Foundry region).')
param location string = resourceGroup().location

param logAnalyticsName string = 'law-ffia-dev'
param appInsightsName string = 'appi-ffia-dev'

@minValue(30)
param retentionInDays int = 30

@description('Daily ingestion cap in GB (cost guard for a demo environment).')
param dailyQuotaGb int = 1

// Public, well-known Azure built-in role definition IDs (same for every tenant), not tenant or
// resource identifiers: Log Analytics Reader, Privileged Monitoring Data Reader (required to
// read GenAI content).
var roleDefinitionGuids = [
  '73c42c96-874c-492b-b04d-ab87d138a893' // leak-scan: allow (built-in role ID, not a secret)
  'dbc9c667-e97f-4491-aee6-90b9cf960190' // leak-scan: allow (built-in role ID, not a secret)
]

resource foundry 'Microsoft.CognitiveServices/accounts@2026-07-01' existing = {
  name: foundryAccountName
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2026-07-01' existing = {
  name: projectName
  parent: foundry
}

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: retentionInDays
    workspaceCapping: { dailyQuotaGb: dailyQuotaGb }
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    IngestionMode: 'LogAnalytics'
  }
}

resource accountConnection 'Microsoft.CognitiveServices/accounts/connections@2026-07-01' = {
  name: '${foundryAccountName}-appinsights'
  parent: foundry
  properties: {
    category: 'AppInsights'
    target: appInsights.id
    authType: 'ApiKey'
    isSharedToAll: true
    credentials: { key: appInsights.properties.ConnectionString }
    metadata: { ApiType: 'Azure', ResourceId: appInsights.id }
  }
}

resource projectConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2026-07-01' = {
  name: appInsightsName
  parent: project
  properties: {
    category: 'AppInsights'
    target: appInsights.id
    authType: 'ApiKey'
    isSharedToAll: true
    credentials: { key: appInsights.properties.ConnectionString }
    metadata: { ApiType: 'Azure', ResourceId: appInsights.id }
  }
}

resource readerRoles 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for roleGuid in roleDefinitionGuids: {
    scope: appInsights
    name: guid(project.id, roleGuid, appInsights.id)
    properties: {
      principalId: project.identity.principalId
      roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleGuid)
      principalType: 'ServicePrincipal'
    }
  }
]

resource foundryDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'to-${logAnalyticsName}'
  scope: foundry
  properties: {
    workspaceId: logAnalytics.id
    logs: [{ categoryGroup: 'allLogs', enabled: true }]
    metrics: [{ category: 'AllMetrics', enabled: true }]
  }
}

output appInsightsId string = appInsights.id
output logAnalyticsId string = logAnalytics.id
