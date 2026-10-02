import type { FAQ } from "@/lib/api-types";
import { RichText } from "@/components/ui/RichText";
export function FaqList({ items }: { items: FAQ[] }) {
  return (
    <div>
      {items.map((item, index) => (
        <details key={index} className="border-b border-border py-5">
          <summary className="cursor-pointer text-lg font-semibold">
            {item.question}
          </summary>
          <div className="pt-5">
            <RichText html={item.answer} />
          </div>
        </details>
      ))}
    </div>
  );
}
