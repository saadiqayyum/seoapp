import {
  MessageSquare,
  Globe,
  Video,
  Image,
  MapPin,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { SerpFeatures } from "@/lib/types";

interface SerpFeaturesIconsProps {
  features: SerpFeatures;
}

const featureConfig = [
  {
    key: "has_featured_snippet" as const,
    label: "Featured Snippet",
    icon: MessageSquare,
  },
  {
    key: "has_knowledge_panel" as const,
    label: "Knowledge Panel",
    icon: Globe,
  },
  {
    key: "has_video_carousel" as const,
    label: "Video Carousel",
    icon: Video,
  },
  { key: "has_image_pack" as const, label: "Image Pack", icon: Image },
  { key: "has_local_pack" as const, label: "Local Pack", icon: MapPin },
];

export function SerpFeaturesIcons({ features }: SerpFeaturesIconsProps) {
  const activeFeatures = featureConfig.filter((f) => features[f.key]);

  if (activeFeatures.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No SERP features detected</p>
    );
  }

  return (
    <div className="flex flex-wrap gap-2">
      {activeFeatures.map((f) => (
        <Tooltip key={f.key}>
          <TooltipTrigger>
            <Badge variant="secondary" className="gap-1.5 px-2.5 py-1">
              <f.icon className="h-3.5 w-3.5" />
              {f.label}
            </Badge>
          </TooltipTrigger>
          <TooltipContent>
            <p>{f.label} appears in SERP for this keyword</p>
          </TooltipContent>
        </Tooltip>
      ))}
    </div>
  );
}
