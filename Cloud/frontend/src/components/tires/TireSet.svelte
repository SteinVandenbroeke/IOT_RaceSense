<script lang="ts">
    import Tire from './Tire.svelte';

    export type CornerData = {
        FL: number; // Front Left
        FR: number; // Front Right
        RL: number; // Rear Left
        RR: number; // Rear Right
    };

    interface Props {
        layout?: 'horizontal' | 'vertical' | 'auto';
        layerCount?: number;
        surfaceTemp?: CornerData | number;
        pressure?: CornerData | number;
        speed?: CornerData | number;
        demo?: boolean;
    }

    let {
        layout = 'auto',
        layerCount = 3,
        demo = false,
        surfaceTemp = { FL: 0, FR: 0, RL: 0, RR: 0 },
        pressure = { FL: 0, FR: 0, RL: 0, RR: 0 },
        speed = { FL: 0, FR: 0, RL: 0, RR: 0 },
    }: Props = $props();

    // Default to a desktop width so it renders correctly on first load
    let innerWidth = $state(1024); 

    // Automatically switch to 'vertical' if the screen is smaller than 768px
    let activeLayout = $derived(
        layout === 'auto' 
            ? (innerWidth < 768 ? 'vertical' : 'horizontal') 
            : layout
    );

    function getCorner(data: CornerData | number, corner: keyof CornerData): number {
        if (typeof data === 'number') return data;
        return data[corner] || 0;
    }
</script>

<svelte:window bind:innerWidth />

<div class="grid grid-cols-2 gap-x-4 sm:gap-x-6 gap-y-6 p-4 sm:p-5 max-w-2xl mx-auto">
    {#if activeLayout === 'horizontal'}
        <Tire statsPosition="left" {layerCount} {demo}
            surfaceTemp={getCorner(surfaceTemp, 'FL')}
            pressure={getCorner(pressure, 'FL')}
            speed={getCorner(speed, 'FL')}
        />
        <Tire statsPosition="right" {layerCount} {demo}
            surfaceTemp={getCorner(surfaceTemp, 'FR')}
            pressure={getCorner(pressure, 'FR')}
            speed={getCorner(speed, 'FR')}
        />

        <Tire statsPosition="left" {layerCount} {demo}
            surfaceTemp={getCorner(surfaceTemp, 'RL')}
            pressure={getCorner(pressure, 'RL')}
            speed={getCorner(speed, 'RL')}
        />
        <Tire statsPosition="right" {layerCount} {demo}
            surfaceTemp={getCorner(surfaceTemp, 'RR')}
            pressure={getCorner(pressure, 'RR')}
            speed={getCorner(speed, 'RR')}
        />
    {:else}
        <Tire statsPosition="top" {layerCount} {demo}
            surfaceTemp={getCorner(surfaceTemp, 'FL')}
            pressure={getCorner(pressure, 'FL')}
            speed={getCorner(speed, 'FL')}
        />
        <Tire statsPosition="top" {layerCount} {demo}
            surfaceTemp={getCorner(surfaceTemp, 'FR')}
            pressure={getCorner(pressure, 'FR')}
            speed={getCorner(speed, 'FR')}
        />

        <Tire statsPosition="bottom" {layerCount} {demo}
            surfaceTemp={getCorner(surfaceTemp, 'RL')}
            pressure={getCorner(pressure, 'RL')}
            speed={getCorner(speed, 'RL')}
        />
        <Tire statsPosition="bottom" {layerCount} {demo}
            surfaceTemp={getCorner(surfaceTemp, 'RR')}
            pressure={getCorner(pressure, 'RR')}
            speed={getCorner(speed, 'RR')}
        />
    {/if}
</div>