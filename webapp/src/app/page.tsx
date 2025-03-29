import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "@/components/ui/resizable";

export default function Home() {
  return (
    <ResizablePanelGroup direction="horizontal">
      <ResizablePanel>One</ResizablePanel>
      <ResizableHandle withHandle />
      <ResizablePanel>Two</ResizablePanel>
    </ResizablePanelGroup>
  );
}
