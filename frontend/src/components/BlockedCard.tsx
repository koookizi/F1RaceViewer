type BlockedCardProps = {
    title: string;
    reason: string;
};

export function BlockedCard({ title, reason }: BlockedCardProps) {
    return (
        <div className="card w-auto bg-warning text-warning-content shadow-xl">
            <div className="card-body text-center">
                <h2 className="card-title justify-center">{title}</h2>
                <p>{reason}</p>
            </div>
        </div>
    );
}
