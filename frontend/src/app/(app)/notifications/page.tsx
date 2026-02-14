"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { formatDistanceToNow } from "date-fns";
import { Bell, CheckCheck } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { api } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { Notification } from "@/types";

export default function NotificationsPage() {
  const { token } = useAuth();
  const queryClient = useQueryClient();

  const { data: notifications, isLoading } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => api.listNotifications(token!) as Promise<Notification[]>,
    enabled: !!token,
  });

  const markReadMutation = useMutation({
    mutationFn: (id: string) => api.markRead(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["unread-count"] });
    },
  });

  const markAllReadMutation = useMutation({
    mutationFn: () => api.markAllRead(token!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["unread-count"] });
    },
  });

  const unreadCount = notifications?.filter((n) => !n.is_read).length ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Notifications</h1>
          <p className="text-muted-foreground">
            {unreadCount > 0 ? `${unreadCount} unread` : "All caught up"}
          </p>
        </div>
        {unreadCount > 0 && (
          <Button
            variant="outline"
            onClick={() => markAllReadMutation.mutate()}
            disabled={markAllReadMutation.isPending}
          >
            <CheckCheck className="mr-1 h-4 w-4" />
            Mark all read
          </Button>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-20" />
          ))}
        </div>
      ) : notifications?.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Bell className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">No notifications yet</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {notifications?.map((n) => (
            <Card
              key={n.id}
              className={cn(
                "cursor-pointer transition-colors hover:bg-accent/50",
                !n.is_read && "border-primary/50 bg-primary/5"
              )}
              onClick={() => {
                if (!n.is_read) markReadMutation.mutate(n.id);
              }}
            >
              <CardContent className="flex items-start gap-3 p-4">
                <div
                  className={cn(
                    "mt-1 h-2 w-2 rounded-full shrink-0",
                    n.is_read ? "bg-transparent" : "bg-primary"
                  )}
                />
                <div className="flex-1 min-w-0">
                  <p className="font-medium">{n.title}</p>
                  <p className="text-sm text-muted-foreground line-clamp-2">{n.message}</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {formatDistanceToNow(new Date(n.created_at), { addSuffix: true })}
                  </p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
