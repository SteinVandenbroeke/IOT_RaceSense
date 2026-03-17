<script lang="ts">
	import SensorCard from '../components/SensorCard.svelte';
	import TyreWidget from '../components/Tyres.svelte';
</script>

<section aria-labelledby="live-telemetry-heading" class="space-y-8 max-w-7xl mx-auto">
	<header>s
		<h1 id="live-telemetry-heading" class="text-2xl font-black text-white">Live Telemetry</h1>
		<p class="text-zinc-400 text-sm">Vehicle 04 - Currently on track</p>
	</header>

	<div>
		<h2 class="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-3">General Metrics</h2>
		<ul class="grid grid-cols-1 md:grid-cols-3 gap-4">
			<li><SensorCard title="Current Speed" value={184} unit="km/h" status="normal" /></li>
			<li><SensorCard title="RPM" value="6,400" unit="rev/min" status="warning" /></li>
			<li><SensorCard title="Brake Bias" value={54} unit="%" status="normal" /></li>
		</ul>
	</div>

	<div>
		<h2 class="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-3">Tyre Status</h2>
		<ul class="grid grid-cols-1 sm:grid-cols-2 gap-4">
			<li>
				<TyreWidget title="Front Left (FL)" temp={112} tempStat="hot" pressure={1.9} presStat="high" />
			</li>
			<li>
				<TyreWidget title="Front Right (FR)" temp={103} tempStat="normal" pressure={1.7} presStat="normal" />
			</li>
			<li>
				<TyreWidget title="Rear Left (RL)" temp={98} tempStat="normal" pressure={1.6} presStat="normal" />
			</li>
			<li>
				<TyreWidget title="Rear Right (RR)" temp={97} tempStat="normal" pressure={0.8} presStat="flat" />
			</li>
		</ul>
	</div>
</section>