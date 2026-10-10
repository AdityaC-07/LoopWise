import { categoryColor } from '../utils/display';

interface MaterialBadgeProps {
  category: string;
}

export function MaterialBadge({ category }: MaterialBadgeProps) {
  const color = categoryColor(category);
  return (
    <span
      className="badge"
      style={{
        background: `color-mix(in srgb, ${color} 20%, transparent)`,
        color,
      }}
    >
      {category}
    </span>
  );
}
