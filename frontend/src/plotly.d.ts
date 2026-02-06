declare module "plotly.js-dist-min" {
    const Plotly: any;
    export default Plotly;
}

declare module "file-saver" {
    export function saveAs(
        data: Blob | File | string,
        filename?: string,
        options?: any,
    ): void;
}
