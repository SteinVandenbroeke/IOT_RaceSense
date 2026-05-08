<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import * as echarts from 'echarts';

	// Grab URL Parameters
	let sessionId = $derived($page.url.searchParams.get('session'));
	let carId = $derived($page.url.searchParams.get('car'));

	let isLoading = $state(true);
	let error = $state<string | null>(null);
	let telemetryData = $state<any>(null);

	onMount(async () => {
		if (!sessionId || !carId) {
			error = "Please select a session and car from the Overview page.";
			isLoading = false;
			return;
		}

		try {
			const res = await fetch(`/api/analytics/${sessionId}/${carId}`);
			if (!res.ok) throw new Error("Failed to fetch analytics data");
			telemetryData = await res.json();
		} catch (err: any) {
			error = err.message;
		} finally {
			isLoading = false;
		}
	});

	// --- CHART 1: TRACTION CIRCLE (Scatter) ---
	function initTractionCircle(node: HTMLElement) {
		const chart = echarts.init(node);
		chart.setOption({
			backgroundColor: 'transparent',
			tooltip: { formatter: 'Lat: {c0}G<br />Lon: {c1}G', backgroundColor: 'rgba(24,24,27,0.9)', textStyle: { color: '#e4e4e7' } },
			grid: { left: '10%', right: '10%', bottom: '10%', top: '10%', containLabel: true },
			xAxis: {
				type: 'value', name: 'Lateral G', nameLocation: 'middle', nameGap: 25,
				min: -3, max: 3, splitLine: { lineStyle: { color: '#27272a' } }, axisLabel: { color: '#71717a' }
			},
			yAxis: {
				type: 'value', name: 'Longitudinal G', nameLocation: 'middle', nameGap: 35,
				min: -3, max: 3, splitLine: { lineStyle: { color: '#27272a' } }, axisLabel: { color: '#71717a' }
			},
			series: [{
				type: 'scatter',
				symbolSize: 6,
				itemStyle: { color: '#34d399', opacity: 0.6 },
				data: telemetryData.traction_circle
			}]
		});
		window.addEventListener('resize', () => chart.resize());
		return { destroy() { chart.dispose(); } };
	}

	// --- CHART 2: CHASSIS DYNAMICS (Line) ---
	function initChassisDynamics(node: HTMLElement) {
		const chart = echarts.init(node);
		chart.setOption({
			backgroundColor: 'transparent',
			tooltip: { trigger: 'axis', backgroundColor: 'rgba(24,24,27,0.9)', textStyle: { color: '#e4e4e7' } },
			legend: { data: ['Roll (deg)', 'Pitch (deg)'], textStyle: { color: '#a1a1aa' } },
			grid: { left: '3%', right: '4%', bottom: '10%', containLabel: true },
			xAxis: { type: 'category', boundaryGap: false, data: telemetryData.timestamps, axisLabel: { color: '#71717a' }, name: 'Time (s)', nameLocation: 'middle', nameGap: 25 },
			yAxis: { type: 'value', name: 'Degrees', axisLabel: { color: '#71717a' }, splitLine: { lineStyle: { color: '#27272a' } } },
			series: [
				{ name: 'Roll (deg)', type: 'line', smooth: true, symbol: 'none', lineStyle: { width: 2, color: '#3b82f6' }, data: telemetryData.roll },
				{ name: 'Pitch (deg)', type: 'line', smooth: true, symbol: 'none', lineStyle: { width: 2, color: '#f59e0b' }, data: telemetryData.pitch }
			]
		});
		window.addEventListener('resize', () => chart.resize());
		return { destroy() { chart.dispose(); } };
	}

	// --- CHART 3: TIRE THERMODYNAMICS (Line) ---
	function initTireThermodynamics(node: HTMLElement) {
		const chart = echarts.init(node);
		chart.setOption({
			backgroundColor: 'transparent',
			tooltip: { trigger: 'axis', backgroundColor: 'rgba(24,24,27,0.9)', textStyle: { color: '#e4e4e7' } },
			legend: { data: ['Surface Temp (°C)', 'Pressure (bar)'], textStyle: { color: '#a1a1aa' } },
			grid: { left: '3%', right: '3%', bottom: '10%', containLabel: true },
			xAxis: { type: 'category', boundaryGap: false, data: telemetryData.timestamps, axisLabel: { color: '#71717a' }, name: 'Time (s)', nameLocation: 'middle', nameGap: 25 },
			yAxis: [
				{ type: 'value', name: 'Temp (°C)', axisLabel: { color: '#ef4444' }, splitLine: { lineStyle: { color: '#27272a' } } },
				{ type: 'value', name: 'Pressure (bar)', axisLabel: { color: '#34d399' }, splitLine: { show: false } }
			],
			series: [
				{ name: 'Surface Temp (°C)', type: 'line', yAxisIndex: 0, smooth: true, symbol: 'none', lineStyle: { width: 2, color: '#ef4444' }, data: telemetryData.temp },
				{ name: 'Pressure (bar)', type: 'line', yAxisIndex: 1, smooth: true, symbol: 'none', lineStyle: { width: 2, color: '#34d399', type: 'dotted' }, data: telemetryData.pressure }
			]
		});
		window.addEventListener('resize', () => chart.resize());
		return { destroy() { chart.dispose(); } };
	}

	// --- CHART 4: SUSPENSION HARSHNESS (Vertical G) ---
	function initSuspensionHarshness(node: HTMLElement) {
		const chart = echarts.init(node);
		chart.setOption({
			backgroundColor: 'transparent',
			tooltip: { trigger: 'axis', backgroundColor: 'rgba(24,24,27,0.9)', textStyle: { color: '#e4e4e7' } },
			grid: { left: '3%', right: '4%', bottom: '10%', containLabel: true },
			xAxis: { type: 'category', boundaryGap: false, data: telemetryData.timestamps, axisLabel: { color: '#71717a' }, name: 'Time (s)', nameLocation: 'middle', nameGap: 25 },
			yAxis: { type: 'value', name: 'Vertical G (Z-Axis)', axisLabel: { color: '#71717a' }, splitLine: { lineStyle: { color: '#27272a' } } },

			// This automatically turns the line RED when it exceeds safe limits!
			visualMap: {
				top: 0, right: 0,
				pieces: [
					{ gt: 1.5, color: '#ef4444' },          // Red for harsh positive (bump)
					{ lt: -1.5, color: '#ef4444' },         // Red for harsh negative (bottom out)
					{ gte: -1.5, lte: 1.5, color: '#3b82f6' } // Blue for normal driving
				],
				outOfRange: { color: '#999' },
				textStyle: { color: '#a1a1aa' }
			},
			series: [
				{
					name: 'Vertical G',
					type: 'line',
					data: telemetryData.vertical_g,
					markLine: {
						silent: true,
						lineStyle: { color: '#ef4444', type: 'dashed', opacity: 0.5 },
						data: [{ yAxis: 1.5, name: 'Bump Limit' }, { yAxis: -1.5, name: 'Drop Limit' }]
					}
				}
			]
		});
		window.addEventListener('resize', () => chart.resize());
		return { destroy() { chart.dispose(); } };
	}
</script>

<section class="max-w-7xl mx-auto space-y-8 p-4 sm:p-6 lg:p-8">
	<header class="flex justify-between items-end border-b border-zinc-800 pb-6">
		<div>
			<h1 class="text-3xl font-black text-white tracking-tight">Lap Analytics</h1>
			<p class="text-zinc-400 text-sm mt-1">
				{#if sessionId && carId}
					Session: #{sessionId} | Vehicle: #{carId.toString().padStart(2, '0')}
				{:else}
					Select a vehicle to view analytics.
				{/if}
			</p>
		</div>
		<a href="/" class="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white text-xs font-bold uppercase rounded transition-colors">
			&larr; Back to Fleet
		</a>
	</header>

	{#if isLoading}
		<div class="flex justify-center py-20 text-emerald-500"><svg class="w-8 h-8 animate-spin" fill="none" viewBox="0 0 24 24"><path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v2m0 12v2m8-8h-2M6 12H4m13.414-5.657l-1.414 1.414M7.414 17.657l-1.414 1.414m0-11.314l1.414 1.414m11.314 11.314l-1.414-1.414"></path></svg></div>
	{:else if error}
		<div class="p-6 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl text-center">{error}</div>
	{:else if telemetryData && telemetryData.timestamps.length > 0}

		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
			<div class="bg-zinc-900 border border-zinc-800 rounded-xl p-4 sm:p-6 shadow-lg">
				<h2 class="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-2">Traction Circle (G-Force)</h2>
				<p class="text-[10px] text-zinc-400 mb-4">Lateral vs Longitudinal Acceleration Grip Utilization.</p>
				<div class="w-full h-[400px]" use:initTractionCircle></div>
			</div>

			<div class="bg-zinc-900 border border-zinc-800 rounded-xl p-4 sm:p-6 shadow-lg">
				<h2 class="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-2">Tire Thermodynamics</h2>
				<p class="text-[10px] text-zinc-400 mb-4">Correlation between surface temperature and casing pressure over time.</p>
				<div class="w-full h-[400px]" use:initTireThermodynamics></div>
			</div>
		</div>

		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
			<div class="bg-zinc-900 border border-zinc-800 rounded-xl p-4 sm:p-6 shadow-lg">
				<h2 class="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-2">Chassis Dynamics</h2>
				<p class="text-[10px] text-zinc-400 mb-4">Body roll and pitch degrees throughout the session.</p>
				<div class="w-full h-[350px]" use:initChassisDynamics></div>
			</div>

			<div class="bg-zinc-900 border border-zinc-800 rounded-xl p-4 sm:p-6 shadow-lg">
				<h2 class="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-2">Suspension & Kerb Strikes</h2>
				<p class="text-[10px] text-zinc-400 mb-4">Vertical G-Force (Z-Axis). Values exceeding ±1.5G indicate harsh impacts or bottoming out.</p>
				<div class="w-full h-[350px]" use:initSuspensionHarshness></div>
			</div>
		</div>

	{:else}
		<div class="text-center py-12 border border-zinc-800 border-dashed rounded-xl text-zinc-500 font-mono">
			No telemetry data found for this car in this session.
		</div>
	{/if}
</section>