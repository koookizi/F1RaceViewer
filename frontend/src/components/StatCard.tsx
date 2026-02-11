type StatCardProps = {
    value: number | string;
    title: string;
};

export default function StatCard({ value, title }: StatCardProps) {
    return (
        <div
            className="card w-auto h-20 border border-slate-300
                 bg-gradient-to-br from-white via-slate-300 to-slate-400
                 text-slate-900 shadow-lg"
        >
            <div className="card-body p-2 flex justify-center">
                <div className="flex flex-col items-start justify-center h-full ps-2">
                    <div className="font-medium text-3xl leading-none mb-1">{value}</div>
                    <div className="text-sm font-medium text-slate-700 leading-tight">{title}</div>
                </div>
            </div>
        </div>
    );
}
