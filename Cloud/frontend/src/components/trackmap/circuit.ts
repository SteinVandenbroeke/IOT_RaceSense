export interface Circuit {
    id: string;
    name: string;
    city: string;
    country: string;
    lengthKm: string;
    corners: string;
    firstGp: string;
    racesHeld: string;
    lapRecord: { time: string; driver: string; year: string; };
    svgFile: string;
    svgReverse: boolean;
}