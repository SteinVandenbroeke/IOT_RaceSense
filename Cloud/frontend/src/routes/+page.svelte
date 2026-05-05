<script lang="ts">
	import { onMount } from 'svelte';

	// 1. Define our State
	let sessions = $state<any[]>([]);
	let expandedSessions = $state<number[]>([]);
	let isLoading = $state(true);
	let error = $state<string | null>(null);

	// 2. Fetch from the Database when the page loads
	onMount(async () => {
		try {
			const res = await fetch('/api/sessions');
			if (!res.ok) throw new Error(`Backend returned ${res.status}`);

			sessions = await res.json();

			// Automatically expand any sessions marked as 'Active'
			expandedSessions = sessions
				.filter(s => s.status === 'Active')
				.map(s => s.id);

		} catch (err: any) {
			console.error("Failed to load sessions:", err);
			error = err.message || "Failed to load database history.";
		} finally {
			isLoading = false;
		}
	});

	function toggleSession(id: number) {
		if (expandedSessions.includes(id)) {
			expandedSessions = expandedSessions.filter(sessionId => sessionId !== id);
		} else {
			expandedSessions = [...expandedSessions, id];
		}
	}
</script>

<section aria-labelledby="overview-heading" class="max-w-5xl mx-auto space-y-8">
	<header>
		<h1 id="overview-heading" class="text-3xl font-black text-white tracking-tight">Session Fleet</h1>
		<p class="text-zinc-400 text-sm mt-1">Select an active car to follow live, or analyze past telemetry.</p>
	</header>

	<!-- Loading State -->
	{#if isLoading}
		<div class="flex flex-col items-center justify-center py-20 text-zinc-500 font-mono space-y-4">
			<svg class="w-8 h-8 animate-spin text-emerald-500" fill="none" viewBox="0 0 24 24">
				<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v2m0 12v2m8-8h-2M6 12H4m13.414-5.657l-1.414 1.414M7.414 17.657l-1.414 1.414m0-11.314l1.414 1.414m11.314 11.314l-1.414-1.414"></path>
			</svg>
			<span>Querying PostgreSQL Data Lake...</span>
		</div>

	<!-- Error State -->
	{:else if error}
		<div class="bg-red-500/10 border border-red-500/20 rounded-xl p-6 text-center">
			<h3 class="text-red-400 font-bold mb-2">Connection Error</h3>
			<p class="text-zinc-400 text-sm">{error}</p>
			<button
				onclick={() => window.location.reload()}
				class="mt-4 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white text-xs font-bold uppercase rounded transition-colors"
			>
				Retry Connection
			</button>
		</div>

	<!-- Loaded State -->
	{:else}
		<div class="space-y-4">
			{#if sessions.length === 0}
				<div class="text-center py-12 border border-zinc-800 border-dashed rounded-xl">
					<p class="text-zinc-500 font-mono">No telemetry sessions found in the database.</p>
				</div>
			{/if}

			{#each sessions as session}
				{@const isActive = session.status === 'Active'}
				{@const isExpanded = expandedSessions.includes(session.id)}

				<div class="bg-zinc-900 border rounded-xl overflow-hidden transition-colors duration-300
					{isActive ? 'border-emerald-500/50 shadow-[0_0_15px_rgba(16,185,129,0.1)]' : 'border-zinc-800'}"
				>
					<button
						class="w-full px-6 py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:bg-zinc-800/50 transition-colors"
						onclick={() => toggleSession(session.id)}
					>
						<div class="flex items-center gap-4">
							<div class="flex items-center justify-center w-10 h-10 rounded-lg bg-zinc-950 border border-zinc-800 font-mono text-sm font-bold text-zinc-300">
								#{session.id}
							</div>
							<div class="text-left">
								<h2 class="font-bold text-white flex items-center gap-2">
									{session.track}
									{#if isActive}
										<span class="flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
											<span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
											Live Now
										</span>
									{:else}
										<span class="text-xs font-normal text-zinc-500 px-2 py-0.5 rounded bg-zinc-800">{session.type}</span>
									{/if}
								</h2>
								<p class="text-xs text-zinc-400 mt-0.5">{session.date} • {session.cars.length} Cars Recorded</p>
							</div>
						</div>

						<div class="text-zinc-500 transition-transform duration-300 {isExpanded ? 'rotate-180' : ''}">
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
						</div>
					</button>

					{#if isExpanded}
						<div class="border-t border-zinc-800/50 bg-zinc-950/30 p-6 animate-in slide-in-from-top-2 duration-200">
							<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

								{#each session.cars as car}
									<div class="bg-zinc-900 border border-zinc-800 rounded-lg p-4 flex flex-col justify-between hover:border-zinc-700 transition-colors">
										<div class="flex justify-between items-start mb-4">
											<div>
												<span class="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Vehicle</span>
												<h3 class="text-xl font-black text-white font-mono">CAR {car.id.toString().padStart(2, '0')}</h3>
											</div>
											{#if isActive}
												<div class="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_#10b981]"></div>
											{/if}
										</div>

										<div class="grid grid-cols-2 gap-4 mb-4">
											<div>
												<span class="block text-[10px] text-zinc-500 uppercase">Telemetry Packets</span>
												<span class="font-mono text-sm text-zinc-300">{car.laps}</span>
											</div>
											<div>
												<span class="block text-[10px] text-zinc-500 uppercase">Top Speed</span>
												<span class="font-mono text-sm text-zinc-300">{car.topSpeed} km/h</span>
											</div>
										</div>

										{#if isActive}
											<a
												href="/live?car={car.id}"
												class="w-full block text-center px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-zinc-950 text-xs font-black uppercase tracking-wider rounded transition-colors"
											>
												Follow Live
											</a>
										{:else}
											<a
												href="/analytics?session={session.id}&car={car.id}"
												class="w-full block text-center px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white text-xs font-bold uppercase tracking-wider rounded transition-colors"
											>
												View Analytics
											</a>
										{/if}
									</div>
								{/each}

							</div>
						</div>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</section>