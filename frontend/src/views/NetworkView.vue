<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useApiStore } from '../stores/api'
import type { NetworkNode, NetworkEdge } from '../types/network'
import { getRepoEdges, rebuildGraph, getGraphStatus, type GraphEdge } from '../api/graph'
import VChart from 'vue-echarts'
import * as echarts from 'echarts/core'
import { GraphChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsOption } from 'echarts/core'

// Register required ECharts components
echarts.use([
  GraphChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  CanvasRenderer
])

const apiStore = useApiStore()
const chartOption = ref<EChartsOption>()
const loading = ref(true)
const error = ref<string | null>(null)
const selectedNode = ref<NetworkNode | null>(null)
const rebuilding = ref(false)
const graphStatus = ref<any>(null)

// Edge type filters
const edgeTypes = ref({
  author: true,
  ecosystem: true,
  collection: true
})

// Get active edge types as comma-separated string
function getActiveEdgeTypes(): string {
  const active = Object.entries(edgeTypes.value)
    .filter(([_, active]) => active)
    .map(([type, _]) => type)
  return active.join(',')
}

async function loadNetwork() {
  loading.value = true
  error.value = null
  try {
    const data = await apiStore.fetchNetworkGraph()

    // Check for empty data
    if (!data.nodes || data.nodes.length === 0) {
      error.value = 'No network data available. Please initialize the system first.'
      loading.value = false
      return
    }

    const nodes = data.nodes.map(n => ({
      id: n.id,
      name: n.name,
      symbolSize: n.size * 10,
      itemStyle: { color: n.color },
      // Store original data for tooltip
      starCount: n.starCount,
      language: n.language,
      categories: n.categories
    }))

    const edges = data.edges.map(e => ({
      source: e.source,
      target: e.target,
      lineStyle: {
        opacity: e.strength,
        width: e.strength * 3,
        curveness: 0.2
      }
    }))

    chartOption.value = {
      title: {
        text: 'Repository Relationship Network',
        left: 'center'
      },
      tooltip: {
        formatter: (params: any) => {
          if (params.dataType === 'node') {
            const node = params.data as any
            return `
              <b>${node.name}</b><br/>
              Stars: ${node.starCount || 'N/A'}<br/>
              Language: ${node.language || 'N/A'}<br/>
              Categories: ${(node.categories || []).join(', ')}
            `
          }
          if (params.dataType === 'edge') {
            return `Connection Strength: ${(params.data.lineStyle?.opacity * 100).toFixed(0)}%`
          }
          return ''
        }
      },
      legend: [{
        data: data.nodes.map((n: NetworkNode) => n.name),
        top: 30
      }],
      series: [{
        type: 'graph',
        layout: 'force',
        force: {
          repulsion: 200,
          edgeLength: [50, 150],
          gravity: 0.1,
          friction: 0.6
        },
        data: nodes,
        links: edges,
        roam: true,
        scaleLimit: {
          min: 0.3,
          max: 3
        },
        label: {
          show: true,
          position: 'right',
          formatter: '{b}',
          fontSize: 10
        },
        labelLayout: {
          hideOverlap: true
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: {
            width: 4
          },
          itemStyle: {
            borderWidth: 2,
            borderColor: '#333'
          }
        },
        lineStyle: {
          color: 'source',
          curveness: 0.2
        }
      }]
    }
  } catch (e: unknown) {
    console.error('Error loading network:', e)
    let message = 'Failed to load network data'
    if (e instanceof Error) {
      message = e.message
    }
    error.value = message
  } finally {
    loading.value = false
  }
}

async function handleRebuildGraph() {
  rebuilding.value = true
  try {
    const result = await rebuildGraph()
    graphStatus.value = result
    // Reload network after rebuild
    await loadNetwork()
  } catch (e: unknown) {
    console.error('Error rebuilding graph:', e)
    error.value = 'Failed to rebuild graph'
  } finally {
    rebuilding.value = false
  }
}

async function loadGraphStatus() {
  try {
    graphStatus.value = await getGraphStatus()
  } catch (e) {
    console.error('Error loading graph status:', e)
  }
}

function handleEdgeTypeChange() {
  // Reload network when edge types change
  loadNetwork()
}

function handleClick(params: any) {
  if (params.dataType === 'node') {
    selectedNode.value = params.data as NetworkNode
  }
}

onMounted(() => {
  loadNetwork()
  loadGraphStatus()
})
</script>

<template>
  <div class="network-view">
    <div class="p-6">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Repository Network</h1>
          <span class="px-2 py-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200 text-sm font-medium rounded">Beta</span>
        </div>
        <button
          @click="handleRebuildGraph"
          :disabled="rebuilding"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white text-sm font-medium rounded transition-colors"
        >
          {{ rebuilding ? 'Rebuilding...' : 'Rebuild Graph' }}
        </button>
      </div>

      <!-- Graph Status -->
      <div v-if="graphStatus" class="mb-4 p-3 bg-gray-50 dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700">
        <div class="text-sm text-gray-700 dark:text-gray-300">
          <span class="font-medium">Graph Status:</span>
          {{ graphStatus.status || 'Unknown' }}
          <span v-if="graphStatus.edges_count !== undefined" class="ml-3">
            | Edges: {{ graphStatus.edges_count }}
          </span>
        </div>
      </div>

      <!-- Edge Type Filters -->
      <div class="mb-4 p-4 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700">
        <h3 class="text-sm font-medium text-gray-900 dark:text-white mb-3">Filter by Edge Type</h3>
        <div class="flex flex-wrap gap-4">
          <label class="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              v-model="edgeTypes.author"
              @change="handleEdgeTypeChange"
              class="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
            />
            <span class="text-sm text-gray-700 dark:text-gray-300">Author Connections</span>
          </label>
          <label class="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              v-model="edgeTypes.ecosystem"
              @change="handleEdgeTypeChange"
              class="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
            />
            <span class="text-sm text-gray-700 dark:text-gray-300">Ecosystem Dependencies</span>
          </label>
          <label class="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              v-model="edgeTypes.collection"
              @change="handleEdgeTypeChange"
              class="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
            />
            <span class="text-sm text-gray-700 dark:text-gray-300">Collection Membership</span>
          </label>
        </div>
        <div class="mt-2 text-xs text-gray-500 dark:text-gray-400">
          Active filters: {{ getActiveEdgeTypes() || 'None' }}
        </div>
      </div>

      <div v-if="loading" class="text-center py-12">
        <div class="text-gray-600 dark:text-gray-400">Loading network visualization...</div>
      </div>

      <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded mb-4">
        {{ error }}
        <router-link to="/init" class="ml-4 underline">Initialize System</router-link>
      </div>

      <div v-else class="chart-container" style="height: 600px;">
        <v-chart
          :option="chartOption"
          :autoresize="true"
          @click="handleClick"
        />
      </div>

      <div v-if="selectedNode" class="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded">
        <h3 class="font-bold text-gray-900 dark:text-white">{{ selectedNode.name }}</h3>
        <p class="text-gray-700 dark:text-gray-300">Stars: {{ selectedNode.starCount }}</p>
        <p class="text-gray-700 dark:text-gray-300">Language: {{ selectedNode.language || 'N/A' }}</p>
        <p class="text-gray-700 dark:text-gray-300">Categories: {{ selectedNode.categories.join(', ') }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.network-view {
  min-height: 100vh;
  background-color: #f9fafb;
}

.dark .network-view {
  background-color: #111827;
}

.chart-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 16px;
}

.dark .chart-container {
  background: #1f2937;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}
</style>
