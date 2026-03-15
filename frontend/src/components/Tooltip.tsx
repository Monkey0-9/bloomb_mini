import { useState } from 'react';
import {
  useFloating,
  autoUpdate,
  offset,
  flip,
  shift,
  useHover,
  useFocus,
  useDismiss,
  useRole,
  useInteractions,
  FloatingPortal,
} from '@floating-ui/react';
import { AnimatePresence, motion } from 'framer-motion';

interface TooltipProps {
  children: React.ReactNode;
  content: React.ReactNode;
}

const Tooltip = ({ children, content }: TooltipProps) => {
  const [isOpen, setIsOpen] = useState(false);

  const {
    x,
    y,
    strategy,
    refs: { setReference, setFloating },
    context,
  } = useFloating({
    open: isOpen,
    onOpenChange: setIsOpen,
    middleware: [offset(8), flip(), shift()],
    whileElementsMounted: autoUpdate,
  });

  const hover = useHover(context, { move: false });
  const focus = useFocus(context);
  const dismiss = useDismiss(context);
  const role = useRole(context, { role: 'tooltip' });

  const { getReferenceProps, getFloatingProps } = useInteractions([
    hover,
    focus,
    dismiss,
    role,
  ]);

  return (
    <>
      <span
        ref={setReference}
        {...getReferenceProps()}
        className="underline decoration-dotted decoration-text-muted hover:decoration-text-accent cursor-help"
      >
        {children}
      </span>
      <AnimatePresence>
        {isOpen && (
          <FloatingPortal>
            <motion.div
              ref={setFloating}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              style={{
                position: strategy,
                top: y ?? 0,
                left: x ?? 0,
                width: 'max-content',
              }}
              {...getFloatingProps()}
              className="z-[100] max-w-[240px] p-3 text-xs bg-void border border-border-normal rounded shadow-2xl text-text-01 backdrop-blur-md"
            >
              {content}
            </motion.div>
          </FloatingPortal>
        )}
      </AnimatePresence>
    </>
  );
};

export default Tooltip;
