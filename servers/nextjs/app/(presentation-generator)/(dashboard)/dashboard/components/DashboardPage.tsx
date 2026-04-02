"use client";

import React, { useRef, useState, useEffect } from "react";

import { DashboardApi } from "@/app/(presentation-generator)/services/api/dashboard";
import { PresentationGrid } from "@/app/(presentation-generator)/(dashboard)/dashboard/components/PresentationGrid";
import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { PresentationGenerationApi } from "@/app/(presentation-generator)/services/api/presentation-generation";
import { toast } from "sonner";
import { useDispatch } from "react-redux";
import { clearHistory } from "@/store/slices/undoRedoSlice";
import { clearOutlines, setPresentationData, setPresentationId } from "@/store/slices/presentationGeneration";
import { useRouter } from "next/navigation";



const DashboardPage: React.FC = () => {
  const dispatch = useDispatch();
  const router = useRouter();
  const importPptxInputRef = useRef<HTMLInputElement>(null);
  const [presentations, setPresentations] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      await fetchPresentations();
    };
    loadData();
  }, []);

  const fetchPresentations = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await DashboardApi.getPresentations();
      data.sort(
        (a: any, b: any) =>
          new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
      );
      setPresentations(data);
    } catch (err) {
      setError(null);
      setPresentations([]);
    } finally {
      setIsLoading(false);
    }
  };

  const removePresentation = (presentationId: string) => {
    setPresentations((prev: any) =>
      prev ? prev.filter((p: any) => p.id !== presentationId) : []
    );
  };

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
    <div className="min-h-screen  w-full px-6 pb-10 relative">
      <div className="sticky top-0 right-0 z-50 py-[28px]   backdrop-blur mb-4 ">
        <div className="flex xl:flex-row flex-col gap-6 xl:gap-0 items-center justify-between">
          <h3 className=" text-[28px] tracking-[-0.84px] font-unbounded font-normal text-[#101828] flex items-center gap-2">

            Slide Presentations
          </h3>
          <div className="flex  gap-2.5 max-sm:w-full max-md:justify-center max-sm:flex-wrap">
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
              className="inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-[#5141e5] border border-[#5141e5]/30 text-sm font-semibold font-syne hover:bg-[#5141e5]/5"
            >
              Import PPTX
            </button>


            <Link
              href="/generate"
              className="inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-black text-sm font-semibold font-syne shadow-sm hover:shadow-md"
              aria-label="Create new presentation"
              style={{
                borderRadius: "48px",
                background: "linear-gradient(270deg, #D5CAFC 2.4%, #E3D2EB 27.88%, #F4DCD3 69.23%, #FDE4C2 100%)",
              }}
            >

              <span className="hidden md:inline">New presentation</span>
              <span className="md:hidden">New</span>
              <ChevronRight className="w-4 h-4" />
            </Link>
            {/* {
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
            } */}
          </div>
        </div>
      </div>
      <PresentationGrid
        presentations={presentations}
        type="slide"
        isLoading={isLoading}
        error={error}
        onPresentationDeleted={removePresentation}
      />
      <div
        className='fixed z-0 bottom-[-16.5rem] left-0 w-full h-full'
        style={{
          height: "341px",
          borderRadius: '1440px',
          background: 'radial-gradient(5.92% 104.69% at 50% 100%, rgba(122, 90, 248, 0.00) 0%, rgba(255, 255, 255, 0.00) 100%), radial-gradient(50% 50% at 50% 50%, rgba(122, 90, 248, 0.80) 0%, rgba(122, 90, 248, 0.00) 100%)',
        }}
      />
    </div>
  );
};

export default DashboardPage;
