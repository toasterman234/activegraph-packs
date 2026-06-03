import { useState } from "react";
import { useSendChat, getGetTraceQueryKey, getGetGraphQueryKey } from "@workspace/api-client-react";
import { useQueryClient } from "@tanstack/react-query";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send, Bot, User } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

type Message = {
  role: 'user' | 'assistant';
  content: string;
  frame_id?: string;
  new_objects?: string[];
};

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  const sendChat = useSendChat();

  const handleSend = () => {
    if (!input.trim() || sendChat.isPending) return;
    
    const userMsg = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);

    sendChat.mutate({ data: { content: userMsg } }, {
      onSuccess: (res) => {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: res.content,
          frame_id: res.frame_id,
          new_objects: res.new_objects
        }]);
        queryClient.invalidateQueries({ queryKey: getGetTraceQueryKey() });
        queryClient.invalidateQueries({ queryKey: getGetGraphQueryKey() });
      },
      onError: () => {
        toast({ title: "Failed to send message", variant: "destructive" });
        setMessages(prev => [...prev, { role: 'assistant', content: "ERROR: Communication failure." }]);
      }
    });
  };

  return (
    <div className="h-full flex flex-col bg-background max-w-4xl mx-auto border-x border-border">
      <div className="p-4 border-b border-border bg-card">
        <h1 className="text-lg font-mono font-bold text-primary">RUNTIME_INTERFACE</h1>
        <p className="text-xs font-mono text-muted-foreground">Interact directly with the ActiveGraph execution loop</p>
      </div>

      <ScrollArea className="flex-1 p-4">
        <div className="space-y-6">
          {messages.length === 0 && (
            <div className="h-32 flex items-center justify-center text-xs font-mono text-muted-foreground uppercase tracking-widest">
              SYSTEM_AWAITING_INPUT
            </div>
          )}
          
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`w-8 h-8 rounded-none border border-border flex items-center justify-center shrink-0 ${msg.role === 'assistant' ? 'bg-primary/10 text-primary border-primary/30' : 'bg-card'}`}>
                {msg.role === 'assistant' ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
              </div>
              <div className={`flex flex-col gap-2 max-w-[80%] ${msg.role === 'user' ? 'items-end' : ''}`}>
                <div className={`p-3 font-mono text-sm whitespace-pre-wrap border border-border ${msg.role === 'user' ? 'bg-muted' : 'bg-card'}`}>
                  {msg.content}
                </div>
                {msg.role === 'assistant' && (msg.frame_id || (msg.new_objects && msg.new_objects.length > 0)) && (
                  <div className="flex gap-2 text-[10px] font-mono text-muted-foreground">
                    {msg.frame_id && <span className="border border-border bg-background px-2 py-1">FRAME: {msg.frame_id.substring(0,8)}</span>}
                    {msg.new_objects && msg.new_objects.length > 0 && (
                      <span className="border border-border bg-background px-2 py-1 text-primary">
                        + {msg.new_objects.length} OBJECTS
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
          {sendChat.isPending && (
            <div className="flex gap-4">
              <div className="w-8 h-8 rounded-none border border-primary/30 bg-primary/10 flex items-center justify-center shrink-0">
                <div className="w-3 h-3 border-2 border-primary border-t-transparent rounded-full animate-spin" />
              </div>
              <div className="p-3 font-mono text-sm border border-border bg-card text-muted-foreground">
                Processing...
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      <div className="p-4 border-t border-border bg-card">
        <form 
          className="flex gap-2"
          onSubmit={e => {
            e.preventDefault();
            handleSend();
          }}
        >
          <Input 
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="ENTER COMMAND..."
            className="font-mono text-sm rounded-none border-border bg-background h-12 focus-visible:ring-primary focus-visible:border-primary"
            disabled={sendChat.isPending}
          />
          <Button 
            type="submit" 
            className="rounded-none h-12 px-6 bg-primary text-primary-foreground font-mono font-bold hover:bg-primary/90"
            disabled={sendChat.isPending || !input.trim()}
          >
            <Send className="w-4 h-4 mr-2" />
            EXEC
          </Button>
        </form>
      </div>
    </div>
  );
}
