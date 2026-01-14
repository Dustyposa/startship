<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useApiStore } from '../stores/api'
import type { NetworkNode, NetworkEdge } from '../types/network'
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
      itemStyle: { color: n.color }
    }))

    const edges = data.edges.map(e => ({
      source: e.source,
      target: e.target,
      lineStyle: { opacity: e.strength }
    }))

    chartOption.value = {
      title: {
        text: 'Repository Relationship Network',
        left: 'center'
      },
      tooltip: {
        formatter: (params: any) => {
          if (params.dataType === 'node') {
            const node = params.data as NetworkNode
            return `
              <b>${node.name}</b><br/>
              Stars: ${node.starCount}<br/>
              Language: ${node.language || 'N/A'}<br/>
              Categories: ${node.categories.join(', ')}
            `
          }
          if (params.dataType === 'edge') {
            return `Strength: ${params.data.strength}`
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
          gravity: 0.1
        },
        data: nodes,
        links: edges,
        roam: true,
        label: {
          show: true,
          position: 'right',
          formatter: '{b}'
        },
        labelLayout: {
          hideOverlap: true
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: {
            width: 3
          }
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

function handleClick(params: any) {
  if (params.dataType === 'node') {
    selectedNode.value = params.data as NetworkNode
  }
}

onMounted(() => {
  loadNetwork()
})
</script>

<template>
  <div class="network-view">
    <div class="p-6">
      <div class="flex items-center gap-3 mb-4">
        <h1 class="text-2xl font-bold">Repository Network</h1>
        <span class="px-2 py-1 bg-yellow-100 text-yellow-800 text-sm font-medium rounded">Beta</span>
      </div>

      <div v-if="loading" class="text-center py-12">
        <div class="text-gray-600">Loading network visualization...</div>
      </div>

      <div v-else-if="error" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
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

      <div v-if="selectedNode" class="mt-4 p-4 bg-blue-50 rounded">
        <h3 class="font-bold">{{ selectedNode.name }}</h3>
        <p>Stars: {{ selectedNode.starCount }}</p>
        <p>Language: {{ selectedNode.language || 'N/A' }}</p>
        <p>Categories: {{ selectedNode.categories.join(', ') }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.network-view {
  min-height: 100vh;
  background-color: #f9fafb;
}

.chart-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 16px;
}
</style>
