import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { HelpCircle } from "lucide-react";

interface PeopleAlsoAskProps {
  questions: string[];
}

export function PeopleAlsoAsk({ questions }: PeopleAlsoAskProps) {
  if (questions.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm font-medium">
          <HelpCircle className="h-4 w-4" />
          People Also Ask ({questions.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Accordion className="w-full">
          {questions.map((question, i) => (
            <AccordionItem key={i} value={`q-${i}`}>
              <AccordionTrigger className="text-sm">
                {question}
              </AccordionTrigger>
              <AccordionContent>
                <p className="text-sm text-muted-foreground">
                  Consider adding a section to your content that answers this
                  question. Adding FAQ schema markup can help you appear in the
                  PAA box.
                </p>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </CardContent>
    </Card>
  );
}
