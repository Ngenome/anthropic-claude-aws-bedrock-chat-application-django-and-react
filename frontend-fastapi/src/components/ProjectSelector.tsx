import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { useProjects } from "@/hooks/useProjects";
import { TokenUsageBar } from "@/components/TokenUsageBar";

interface ProjectSelectorProps {
  value?: string;
  onValueChange: (value: string) => void;
}

export function ProjectSelector({
  value,
  onValueChange,
}: ProjectSelectorProps) {
  const { data: projects, isLoading } = useProjects();

  if (isLoading) return null;

  return (
    <div className="space-y-4">
      <Select value={value} onValueChange={onValueChange}>
        <SelectTrigger>
          <SelectValue placeholder="Select a project context" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="none">No Project Context</SelectItem>
          {projects?.map((project) => (
            <SelectItem key={project.id} value={project.id.toString()}>
              {project.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {value &&
        value !== "none" &&
        projects?.find((p) => p.id.toString() === value) && (
          <div className="p-4 border rounded-lg bg-gray-50 dark:bg-gray-900">
            <h4 className="font-medium mb-2">Project Knowledge Base</h4>
            <TokenUsageBar
              current={
                projects.find((p) => p.id.toString() === value)?.total_tokens ||
                0
              }
              max={160000}
              label="Knowledge Base Usage"
            />
          </div>
        )}
    </div>
  );
}
