"use client";

import { ChevronRight } from 'lucide-react';
import Link from 'next/link';
import React, { useRef } from 'react'
import { defaultNavItems } from './DashboardSidebar';
import { usePathname, useRouter } from 'next/navigation';
import { PresentationGenerationApi } from '../../services/api/presentation-generation';
import { toast } from 'sonner';
import { DashboardApi } from '../../services/api/dashboard';
import { useDispatch } from 'react-redux';
import { clearHistory } from '@/store/slices/undoRedoSlice';
import { clearOutlines, setPresentationData, setPresentationId } from '@/store/slices/presentationGeneration';

const DashboardNav = () => {
    const dispatch = useDispatch();
    const router = useRouter();
    const pathname = usePathname();
    const importPptxInputRef = useRef<HTMLInputElement>(null);
    const activeTab = pathname.split("?")[0].split("/").pop();
    const activeItem = defaultNavItems.find((i: any) => i.key === activeTab);

    const extractPresentationId = (response: any): string | null => {
        return response?.id ?? response?.presentation_id ?? response?.presentationId ?? null;
    };

    const hydrateAndNavigateToPresentation = async (presentationId: string) => {
        const presentation = await DashboardApi.getPresentation(presentationId);
        dispatch(setPresentationId(presentationId));
        dispatch(setPresentationData(presentation));
        dispatch(clearHistory());
        dispatch(clearOutlines());
        router.push(`/presentation?id=${presentationId}`);
    };

    const handleImportPptx = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = event.target.files?.[0];
        event.target.value = "";
        if (!selectedFile) return;

        if (!selectedFile.name.toLowerCase().endsWith(".pptx")) {
            toast.error("Please select a valid PPTX file");
            return;
        }

        try {
            toast.info("Importing PPTX...");
            const importResponse = await PresentationGenerationApi.importPptx(selectedFile);
            const presentationId = extractPresentationId(importResponse);
            if (!presentationId) {
                throw new Error("Import succeeded but no presentation id was returned.");
            }
            await hydrateAndNavigateToPresentation(presentationId);
        } catch (error: any) {
            console.error("Error importing PPTX", error);
            toast.error("PPTX import failed", {
                description: error?.message || "Unable to import PPTX file.",
            });
        }
    };




    return (
        <div className="sticky top-0 right-0 z-50 py-[28px]   backdrop-blur ">
            <div className="flex xl:flex-row flex-col gap-6 xl:gap-0 items-center justify-between">
                <h3 className=" text-[28px] tracking-[-0.84px] font-unbounded font-normal text-[#101828] flex items-center gap-2">

                    {activeItem?.label ?? (activeTab && activeTab?.charAt(0).toUpperCase() + activeTab?.slice(1))}
                </h3>
                <div className="flex  gap-2.5 max-sm:w-full max-md:justify-center max-sm:flex-wrap">
                    {activeTab !== "playground" && activeTab !== "theme" && <>
                        <input
                            ref={importPptxInputRef}
                            type="file"
                            className="hidden"
                            accept=".pptx,application/vnd.openxmlformats-officedocument.presentationml.presentation"
                            onChange={handleImportPptx}
                        />
                        <button
                            type="button"
                            onClick={() => importPptxInputRef.current?.click()}
                            className="inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-[#5141e5] border border-[#5141e5]/30 text-sm font-medium hover:bg-[#5141e5]/5"
                        >
                            Import PPTX
                        </button>
                    </>}



                    {activeTab !== "playground" && activeTab !== "theme" && <Link
                        href="/generate"
                        className="inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-black text-sm font-medium shadow-sm hover:shadow-md"
                        aria-label="Create new presentation"
                        style={{
                            borderRadius: "48px",
                            background: "linear-gradient(270deg, #D5CAFC 2.4%, #E3D2EB 27.88%, #F4DCD3 69.23%, #FDE4C2 100%)",
                        }}
                    >

                        <span className="hidden md:inline">New presentation</span>
                        <span className="md:hidden">New</span>
                        <ChevronRight className="w-4 h-4" />
                    </Link>}
                    {activeTab === "theme" &&
                        <Link
                            href="/theme?tab=new-theme"
                            className="inline-flex items-center font-inter font-normal gap-2 rounded-xl px-4 py-2.5 text-black text-sm  shadow-sm hover:shadow-md"
                            aria-label="Create new themes"
                            style={{
                                borderRadius: "48px",
                                background: "linear-gradient(270deg, #D5CAFC 2.4%, #E3D2EB 27.88%, #F4DCD3 69.23%, #FDE4C2 100%)",
                            }}
                        >
                            <span className="hidden md:inline">New Themes</span>
                            <span className="md:hidden">New</span>
                            <ChevronRight className="w-4 h-4" />
                        </Link>
                    }
                </div>
            </div>
        </div>
    )
}

export default DashboardNav
