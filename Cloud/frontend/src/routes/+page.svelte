<script lang="ts">
	import { onMount } from 'svelte';

	let sessions = $state<any[]>([]);
	let selectedSessionId = $state<number | null>(null);
	let isLoading = $state(true);
	let error = $state<string | null>(null);

	// Dynamically split our data into the "Hero" session and the "Others"
	let selectedSession = $derived(sessions.find(s => s.id === selectedSessionId));
	let otherSessions = $derived(sessions.filter(s => s.id !== selectedSessionId));

	onMount(async () => {
		try {
			const res = await fetch('/api/sessions');
			if (!res.ok) throw new Error(`Backend returned ${res.status}`);

			sessions = await res.json();

			// Auto-select the Active session on load. If none are active, select the newest one.
			if (sessions.length > 0) {
				const activeSession = sessions.find(s => s.status === 'Active');
				selectedSessionId = activeSession ? activeSession.id : sessions[0].id;
			}

		} catch (err: any) {
			console.error("Failed to load sessions:", err);
			error = err.message || "Failed to load database history.";
		} finally {
			isLoading = false;
		}
	});
</script>

<section aria-labelledby="overview-heading" class="w-full max-w-[1600px] mx-auto space-y-8 py-2">
	<header>
		<h1 id="overview-heading" class="text-3xl font-black text-white tracking-tight">Session Fleet</h1>
		<p class="text-zinc-400 text-sm mt-1">Select an active car to follow live, or analyze past telemetry.</p>
	</header>

	{#if isLoading}
		<div class="flex flex-col items-center justify-center py-20 text-zinc-500 font-mono space-y-4">
			<svg class="w-8 h-8 animate-spin text-emerald-500" fill="none" viewBox="0 0 24 24">
				<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v2m0 12v2m8-8h-2M6 12H4m13.414-5.657l-1.414 1.414M7.414 17.657l-1.414 1.414m0-11.314l1.414 1.414m11.314 11.314l-1.414-1.414"></path>
			</svg>
			<span>Querying PostgreSQL Data Lake...</span>
		</div>

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

	{:else}
		{#if sessions.length === 0}
			<div class="text-center py-12 border border-zinc-800 border-dashed rounded-xl">
				<p class="text-zinc-500 font-mono">No telemetry sessions found in the database.</p>
			</div>
		{/if}

		{#if selectedSession}
			{@const isActive = selectedSession.status === 'Active'}

			<div class="bg-zinc-900 border rounded-xl overflow-hidden {isActive ? 'border-emerald-500/50 shadow-[0_0_15px_rgba(16,185,129,0.1)]' : 'border-zinc-800'}">

				<div class="w-full px-6 py-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-zinc-800/50 bg-zinc-950/50">
					<div class="flex items-center gap-4 min-w-0">
						<div class="flex-shrink-0 flex items-center justify-center w-12 h-12 rounded-lg bg-zinc-950 border border-zinc-800 font-mono text-base font-bold text-zinc-300">
							#{selectedSession.id}
						</div>
						<div class="text-left truncate">
							<h2 class="text-xl font-bold text-white flex items-center gap-3 truncate">
								<span class="truncate">{selectedSession.track}</span>
								{#if isActive}
									<span class="flex-shrink-0 flex items-center gap-1.5 px-2.5 py-0.5 rounded text-xs font-black uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
										<span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
										Live Now
									</span>
								{:else}
									<span class="flex-shrink-0 text-xs font-normal text-zinc-500 px-2.5 py-0.5 rounded bg-zinc-800">{selectedSession.type}</span>
								{/if}
							</h2>
							<p class="text-sm text-zinc-400 mt-1 truncate">{selectedSession.date} • {selectedSession.cars.length} Cars Recorded</p>
						</div>
					</div>
				</div>

				<div class="bg-zinc-950 p-0">
					<div class="grid grid-cols-12 gap-4 px-6 py-3 border-b border-zinc-800/50 text-[11px] font-black text-zinc-500 uppercase tracking-widest bg-zinc-900/80">
						<div class="col-span-2 sm:col-span-1">Pos</div>
						<div class="col-span-2 sm:col-span-1">Car</div>
						<div class="col-span-5 sm:col-span-8">Driver / Team</div>
						<div class="col-span-3 sm:col-span-2 text-right">Action</div>
					</div>

					<div class="divide-y divide-zinc-800/50 max-h-[600px] overflow-y-auto scrollbar-thin">
						{#each selectedSession.cars as car, index}
							<div class="grid grid-cols-12 gap-4 px-6 py-3 items-center hover:bg-zinc-800/50 transition-colors group">

								<div class="col-span-2 sm:col-span-1 text-sm font-black {isActive ? 'text-emerald-400' : 'text-zinc-400'}">
									P{index + 1}
								</div>

								<div class="col-span-2 sm:col-span-1 text-base font-mono font-bold text-white">
									#{car.id.toString().padStart(2, '0')}
								</div>

								<div class="col-span-5 sm:col-span-8 text-sm font-medium text-zinc-300 truncate">
									Driver {car.id} <span class="text-xs text-zinc-600 hidden sm:inline ml-2">Team {car.id}</span>
								</div>

								<div class="col-span-3 sm:col-span-2 text-right">
									{#if isActive}
										<a
											href="/live?car={car.id}"
											class="inline-block px-4 py-1.5 bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500 hover:text-zinc-900 border border-emerald-500/20 text-[11px] font-black uppercase tracking-wider rounded transition-colors"
										>
											Live
										</a>
									{:else}
										<a
											href="/analytics?session={selectedSession.id}&car={car.id}"
											class="inline-block px-4 py-1.5 bg-zinc-800 text-zinc-300 hover:bg-zinc-700 hover:text-white border border-zinc-700 text-[11px] font-bold uppercase tracking-wider rounded transition-colors"
										>
											Data
										</a>
									{/if}
								</div>
							</div>
						{/each}
					</div>
				</div>
			</div>
		{/if}

		{#if otherSessions.length > 0}
			<div class="pt-6 border-t border-zinc-800/50">
				<h3 class="text-lg font-bold text-zinc-300 mb-4">Other Sessions</h3>
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
					{#each otherSessions as session}
						{@const isActive = session.status === 'Active'}
						<button
							class="flex items-center gap-4 p-4 rounded-xl border transition-all duration-200 text-left cursor-pointer bg-zinc-950 border-zinc-800 hover:border-zinc-600 hover:bg-zinc-900"
							onclick={() => selectedSessionId = session.id}
						>
							<div class="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-lg bg-zinc-900 border border-zinc-700 font-mono text-sm font-bold {isActive ? 'text-emerald-400' : 'text-zinc-400'}">
								#{session.id}
							</div>
							<div class="min-w-0 flex-1">
								<div class="font-bold text-sm text-white flex items-center gap-2 truncate">
									<span class="truncate">{session.track}</span>
									{#if isActive}
										<span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse flex-shrink-0"></span>
									{/if}
								</div>
								<div class="text-xs text-zinc-500 truncate mt-0.5">{session.date} • {session.cars.length} Cars</div>
							</div>
						</button>
					{/each}
				</div>
			</div>
		{/if}
	{/if}
</section>