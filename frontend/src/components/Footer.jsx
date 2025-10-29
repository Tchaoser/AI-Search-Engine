import React from "react";

export default function Footer() {
    return (
        <div className="flex flex-col justify-between items-center text-sm gap-2 w-full">
            <div>© {new Date().getFullYear()} AI Search Dev</div>
            <div className="flex gap-4">
                {/* TODO: consider adding Privacy, Terms links */}
            </div>
        </div>
    );
}
