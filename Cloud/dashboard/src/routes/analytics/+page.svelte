<script lang="ts">
	import * as echarts from 'echarts';

	// --- GLOBAL STATE ---
	let xAxisMode: 'distance' | 'time' = $state('distance');

	// --- MOCK DATA ---
	// X-Axes
	const distanceData = Array.from({ length: 50 }, (_, i) => i * 20); // 0 to 980 meters
	const timeData = Array.from({ length: 50 }, (_, i) => +(i * 0.4).toFixed(1)); // 0 to 19.6 seconds

	// Y-Axes: Speed
	const bestLapSpeed = [100, 120, 150, 180, 210, 225, 230, 220, 150, 90, 85, 95, 120, 160, 190, 210, 230, 245, 250, 255, 250, 200, 120, 80, 75, 80, 100, 130, 170, 200, 220, 240, 260, 270, 275, 270, 250, 180, 110, 90, 85, 100, 140, 180, 210, 230, 240, 250, 255, 260];
	const currentLapSpeed = [95, 115, 145, 170, 190, 210, 215, 205, 130, 85, 80, 90, 115, 150, 185, 200, 220, 235, 240, 245, 235, 180, 110, 85, 75, 85, 105, 140, 175, 205, 225, 245, 265, 275, 280, 275, 255, 190, 120, 95, 85, 95, 135, 175, 205, 225, 235, 245, 250, 255];

	// Y-Axes: Tires
	const flTemp = [85, 85, 86, 86, 87, 88, 89, 92, 105, 112, 110, 105, 100, 98, 97, 97, 98, 99, 100, 101, 102, 108, 115, 118, 116, 112, 108, 105, 103, 102, 102, 103, 104, 105, 106, 107, 109, 115, 120, 122, 120, 115, 110, 108, 106, 105, 105, 106, 107, 108];
	const flPressure = [1.60, 1.60, 1.60, 1.61, 1.61, 1.62, 1.62, 1.63, 1.65, 1.68, 1.69, 1.68, 1.67, 1.66, 1.66, 1.66, 1.67, 1.67, 1.68, 1.69, 1.70, 1.72, 1.75, 1.78, 1.79, 1.78, 1.76, 1.75, 1.74, 1.74, 1.74, 1.75, 1.76, 1.77, 1.78, 1.79, 1.80, 1.83, 1.86, 1.88, 1.88, 1.87, 1.85, 1.84, 1.83, 1.82, 1.82, 1.83, 1.84, 1.85];

	// --- CHART ACTIONS ---
	// Using Svelte actions so we can surgically update the chart when xAxisMode changes
	function initSpeedChart(node: HTMLElement, mode: 'distance' | 'time') {
		const chart = echarts.init(node);
		
		const getBaseOption = () => ({
			backgroundColor: 'transparent',
			tooltip: { trigger: 'axis', backgroundColor: 'rgba(24, 24, 27, 0.9)', borderColor: '#3f3f46', textStyle: { color: '#e4e4e7' } },
			legend: { data: ['Lap 12 (Best)', 'Lap 14 (Current)'], textStyle: { color: '#a1a1aa' }, top: 0 },
			grid: { left: '3%', right: '4%', bottom: '10%', containLabel: true },
			xAxis: { 
				type: 'category', 
				boundaryGap: false, 
				axisLabel: { color: '#71717a' }, 
				splitLine: { show: true, lineStyle: { color: '#27272a', type: 'dashed' } },
				nameLocation: 'middle',
				nameGap: 30,
				nameTextStyle: { color: '#a1a1aa', fontWeight: 'bold' }
			},
			yAxis: { type: 'value', name: 'Speed (km/h)', axisLabel: { color: '#71717a' }, splitLine: { show: true, lineStyle: { color: '#27272a' } } },
			series: [
				{ name: 'Lap 12 (Best)', type: 'line', smooth: true, symbol: 'none', lineStyle: { width: 3, color: '#34d399' }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(52, 211, 153, 0.3)' }, { offset: 1, color: 'rgba(52, 211, 153, 0)' }]) }, data: bestLapSpeed },
				{ name: 'Lap 14 (Current)', type: 'line', smooth: true, symbol: 'none', lineStyle: { width: 2, color: '#71717a', type: 'dashed' }, data: currentLapSpeed }
			]
		});

		chart.setOption(getBaseOption());

		// Initial set
		chart.setOption({
			xAxis: { data: mode === 'distance' ? distanceData : timeData, name: mode === 'distance' ? 'Distance (m)' : 'Time (s)' }
		});

		window.addEventListener('resize', () => chart.resize());

		return {
			// This runs whenever xAxisMode changes!
			update(newMode: 'distance' | 'time') {
				chart.setOption({
					xAxis: { data: newMode === 'distance' ? distanceData : timeData, name: newMode === 'distance' ? 'Distance (m)' : 'Time (s)' }
				});
			},
			destroy() { chart.dispose(); }
		};
	}

	function initTireChart(node: HTMLElement, mode: 'distance' | 'time') {
		const chart = echarts.init(node);
		
		const getBaseOption = () => ({
			backgroundColor: 'transparent',
			tooltip: { trigger: 'axis', backgroundColor: 'rgba(24, 24, 27, 0.9)', borderColor: '#3f3f46', textStyle: { color: '#e4e4e7' } },
			legend: { data: ['Temperature (°C)', 'Pressure (bar)'], textStyle: { color: '#a1a1aa' }, top: 0 },
			grid: { left: '3%', right: '3%', bottom: '10%', containLabel: true },
			xAxis: { 
				type: 'category', 
				boundaryGap: false, 
				axisLabel: { color: '#71717a' },
				nameLocation: 'middle',
				nameGap: 30,
				nameTextStyle: { color: '#a1a1aa', fontWeight: 'bold' }
			},
			yAxis: [
				{ type: 'value', name: 'Temp (°C)', min: 80, max: 130, axisLabel: { color: '#ef4444' }, nameTextStyle: { color: '#ef4444' }, splitLine: { show: true, lineStyle: { color: '#27272a' } } },
				{ type: 'value', name: 'Pressure (bar)', min: 1.5, max: 2.0, axisLabel: { color: '#3b82f6' }, nameTextStyle: { color: '#3b82f6' }, splitLine: { show: false } }
			],
			series: [
				{ name: 'Temperature (°C)', type: 'line', yAxisIndex: 0, smooth: true, symbol: 'none', lineStyle: { width: 2, color: '#ef4444' }, data: flTemp },
				{ name: 'Pressure (bar)', type: 'line', yAxisIndex: 1, smooth: true, symbol: 'none', lineStyle: { width: 2, color: '#3b82f6', type: 'dotted' }, data: flPressure }
			]
		});

		chart.setOption(getBaseOption());
		chart.setOption({
			xAxis: { data: mode === 'distance' ? distanceData : timeData, name: mode === 'distance' ? 'Distance (m)' : 'Time (s)' }
		});

		window.addEventListener('resize', () => chart.resize());

		return {
			update(newMode: 'distance' | 'time') {
				chart.setOption({
					xAxis: { data: newMode === 'distance' ? distanceData : timeData, name: newMode === 'distance' ? 'Distance (m)' : 'Time (s)' }
				});
			},
			destroy() { chart.dispose(); }
		};
	}
</script>

<section aria-labelledby="analytics-heading" class="max-w-7xl mx-auto space-y-8">
	
	<header class="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4 border-b border-zinc-800 pb-6">
		<div>
			<h1 id="analytics-heading" class="text-3xl font-black text-white tracking-tight">Telemetry Analytics</h1>
			<p class="text-zinc-400 text-sm mt-1">Session: SESS-089 | Spa-Francorchamps</p>
		</div>
		
		<div class="flex items-center gap-4">
			<div class="flex bg-zinc-900 rounded-lg p-1 border border-zinc-800 shadow-inner">
				<button 
					class="px-4 py-1.5 text-xs font-bold uppercase tracking-wider rounded-md transition-all duration-200 {xAxisMode === 'distance' ? 'bg-zinc-700 text-white shadow' : 'text-zinc-500 hover:text-zinc-300'}"
					onclick={() => xAxisMode = 'distance'}
				>
					Distance
				</button>
				<button 
					class="px-4 py-1.5 text-xs font-bold uppercase tracking-wider rounded-md transition-all duration-200 {xAxisMode === 'time' ? 'bg-zinc-700 text-white shadow' : 'text-zinc-500 hover:text-zinc-300'}"
					onclick={() => xAxisMode = 'time'}
				>
					Time
				</button>
			</div>

			<button class="bg-zinc-100 hover:bg-white text-zinc-950 px-4 py-2 rounded-md text-sm font-bold transition-colors">
				Export CSV
			</button>
		</div>
	</header>

	<div class="bg-zinc-900 border border-zinc-800 rounded-xl p-4 sm:p-6 shadow-lg">
		<h2 class="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-6">Speed Trace Comparison</h2>
		
		<div class="w-full h-[350px]" use:initSpeedChart={xAxisMode}></div>

		<div class="mt-6 p-4 bg-zinc-950 rounded-lg border border-zinc-800 flex items-start gap-4">
			<div class="p-2 bg-emerald-500/20 text-emerald-400 rounded-full mt-1">
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
			</div>
			<div>
				<h3 class="text-sm font-bold text-white">Speed Analysis</h3>
				<p class="text-sm text-zinc-400 mt-1 leading-relaxed">
					In the current lap, braking for Turn 1 occurred <span class="text-red-400 font-bold">earlier</span> than the best lap. 
					{#if xAxisMode === 'distance'}
						Visually, this is evident around the <span class="text-zinc-200 font-mono">180m</span> mark where the dashed line drops prematurely, resulting in a 0.2s deficit on corner exit.
					{:else}
						Notice how at <span class="text-zinc-200 font-mono">3.6s</span> the dashed line is significantly lower, showing the time lost from early deceleration.
					{/if}
				</p>
			</div>
		</div>
	</div>

	<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
		<div class="col-span-1 lg:col-span-2 bg-zinc-900 border border-zinc-800 rounded-xl p-4 sm:p-6 shadow-lg">
			<div class="flex justify-between items-center mb-6">
				<h2 class="text-xs font-bold text-zinc-500 uppercase tracking-widest">Tire Thermodynamics (Front Left)</h2>
				<span class="px-2 py-0.5 bg-blue-500/10 text-blue-400 text-[10px] font-bold rounded uppercase tracking-wider border border-blue-500/20">Simulated MVP Data</span>
			</div>
			
			<div class="w-full h-[300px]" use:initTireChart={xAxisMode}></div>
		</div>

		<div class="col-span-1 bg-zinc-900 border border-zinc-800 rounded-xl p-6 shadow-lg flex flex-col">
			<h2 class="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-4">Correlation Analysis</h2>
			<p class="text-sm text-zinc-300 leading-relaxed mb-6">
				By analyzing temperature and pressure together, we can observe the thermal expansion of the air inside the tire casing. 
			</p>
			<div class="space-y-4 flex-1">
				<div class="p-3 bg-zinc-950 rounded-lg border border-zinc-800 border-l-4 border-l-red-500">
					<h3 class="text-xs font-bold text-white uppercase mb-1">Heavy Braking Zones</h3>
					<p class="text-xs text-zinc-400">Rapid deceleration causes friction, spiking the surface temperature over 115°C.</p>
				</div>
				<div class="p-3 bg-zinc-950 rounded-lg border border-zinc-800 border-l-4 border-l-blue-500">
					<h3 class="text-xs font-bold text-white uppercase mb-1">Pressure Lag</h3>
					<p class="text-xs text-zinc-400">Pressure increases steadily behind the temperature spikes, peaking at 1.88 bar, which could lead to a loss of grip.</p>
				</div>
			</div>
		</div>
	</div>
</section>