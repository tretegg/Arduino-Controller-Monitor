<script lang="ts">
    import { onMount, onDestroy, tick} from 'svelte';
    import Chart from 'chart.js/auto';

    let apiUrl = "http://127.0.0.1:8000/api"

    // Variables to hold hardware data
    let hardwareStatus: any = $state(null);
    let pollingInterval: ReturnType<typeof setInterval> | null = null;

    // Chart Variables
    let chartCanvas: HTMLCanvasElement;
    let sensorChart: Chart;
    const MAX_DATA_POINTS = 20;

    // Arrays to hold the historical data for the chart lines
    let timeLabels: string[] = [];
    let ldrTopLeftData: number[] = [];
    let ldrTopRightData: number[] = [];
    let ldrBottomLeftData: number[] = [];
    let ldrBottomRightData: number[] = [];

    // Fetch data from the API
    async function fetchStatus() {
            try {   
                const response = await fetch(`${apiUrl}/status`);
                hardwareStatus = await response.json();

                await tick();
            
                if (!sensorChart && chartCanvas) {
                    initChart();
                }
            
                updateChart(hardwareStatus);
            } catch (error) {
                console.error('Error fetching status:', error);
            }
        }

    // Send command to the API
    async function moveMotor(axis: string, direction: string, steps: number) {
        await fetch(`${apiUrl}/move`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ axis, direction, steps })
        });
    }

    // Update the chart
    function updateChart(data: any) {
        if (!sensorChart) return;

        // Get the current time (e.g., "10:30:15 AM")
        const now = new Date().toLocaleTimeString('en-US', { hour12: false });
        
        // Push the new data onto the end of the arrays
        timeLabels.push(now);
        ldrTopLeftData.push(data.ldr_top_left);
        ldrTopRightData.push(data.ldr_top_right);
        ldrBottomLeftData.push(data.ldr_bottom_left);
        ldrBottomRightData.push(data.ldr_bottom_right);

        // If the array gets too long, chop off the oldest data point at the front
        if (timeLabels.length > MAX_DATA_POINTS) {
            timeLabels.shift();
            ldrTopLeftData.shift();
            ldrTopRightData.shift();
            ldrBottomLeftData.shift();
            ldrBottomRightData.shift();
        }

        // Tell Chart.js to redraw the canvas
        sensorChart.update();
    }

    // Initialize the Chart on our canvas element
    function initChart() {
        if (!chartCanvas) return; // Safety check

        sensorChart = new Chart(chartCanvas, {
            type: 'line',
            data: {
                labels: timeLabels,
                datasets: [
                    { label: 'Top Left', data: ldrTopLeftData, borderColor: '#ef4444', tension: 0.3, borderWidth: 2 },
                    { label: 'Top Right', data: ldrTopRightData, borderColor: '#f87171', tension: 0.3, borderWidth: 2 },
                    { label: 'Bottom Left', data: ldrBottomLeftData, borderColor: '#3b82f6', tension: 0.3, borderWidth: 2 },
                    { label: 'Bottom Right', data: ldrBottomRightData, borderColor: '#60a5fa', tension: 0.3, borderWidth: 2 }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                scales: {
                    y: { 
                        beginAtZero: true, 
                        max: 1023, 
                        grid: { color: '#334155' },
                        ticks: { color: '#94a3b8' }
                    },
                    x: {
                        grid: { color: '#334155' },
                        ticks: { color: '#94a3b8' }
                    }
                },
                plugins: {
                    legend: { labels: { color: '#e2e8f0' } }
                }
            }
        });
    }

    // Start loop
    onMount(() => {
        fetchStatus(); // Fetch initial data
        pollingInterval = setInterval(fetchStatus, 1000); // Poll every second
    });
    
    // Clean up on component destroy
    onDestroy(() => {
        if (pollingInterval) {
            clearInterval(pollingInterval);
        }
        if (sensorChart) {
            sensorChart.destroy();
        }
    });
</script>

<div class="min-h-screen bg-slate-900 text-slate-200 font-sans p-8">
    <main class="max-w-5xl mx-auto">
        <header class="flex justify-between items-center mb-6 border-b border-slate-700 pb-4">
            <h1 class="text-3xl font-bold tracking-tight">Arduino Control Center</h1>
        </header>

        {#if hardwareStatus}
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg lg:col-span-2">
                    <h2 class="text-xl font-semibold mb-4 text-slate-100 flex items-center gap-2">
                        LDR Intensity Stream
                    </h2>
                    <div class="relative h-64 w-full">
                        <canvas bind:this={chartCanvas}></canvas>
                    </div>
                </div>

                <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg flex flex-col justify-between">
                    <div>
                        <h2 class="text-xl font-semibold mb-6 text-slate-100 flex items-center gap-2">
                            Manual Movements
                        </h2>
                        
                        <div class="mb-6">
                            <div class="flex justify-between items-center mb-2">
                                <span class="text-slate-400 text-sm font-bold uppercase tracking-wider">Azimuth</span>
                            </div>
                            <div class="grid grid-cols-2 gap-2">
                                <button onclick={() => moveMotor('azimuth', 'backward', 10)} class="bg-slate-700 text-slate-200 py-2 rounded hover:bg-slate-600 transition-colors font-mono text-sm border border-slate-600 shadow-sm">-10° CCW</button>
                                <button onclick={() => moveMotor('azimuth', 'forward', 10)} class="bg-slate-700 text-slate-200 py-2 rounded hover:bg-slate-600 transition-colors font-mono text-sm border border-slate-600 shadow-sm">+10° CW</button>
                            </div>
                        </div>

                        <div>
                            <div class="flex justify-between items-center mb-2">
                                <span class="text-slate-400 text-sm font-bold uppercase tracking-wider">Elevation</span>
                            </div>
                            <div class="grid grid-cols-2 gap-2">
                                <button onclick={() => moveMotor('elevation', 'backward', 10)} class="bg-slate-700 text-slate-200 py-2 rounded hover:bg-slate-600 transition-colors font-mono text-sm border border-slate-600 shadow-sm">-10° DOWN</button>
                                <button onclick={() => moveMotor('elevation', 'forward', 10)} class="bg-slate-700 text-slate-200 py-2 rounded hover:bg-slate-600 transition-colors font-mono text-sm border border-slate-600 shadow-sm">+10° UP</button>
                            </div>
                        </div>
                    </div>
                </div>

            </div>
        {:else}
            <div class="flex flex-col items-center justify-center h-64 border-2 border-dashed border-slate-700 rounded-xl">
                <p class="text-slate-400 font-mono animate-pulse">Awaiting handshake with Python API on port 8000...</p>
            </div>
        {/if}
    </main>
</div>