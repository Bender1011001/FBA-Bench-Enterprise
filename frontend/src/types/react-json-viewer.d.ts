declare module 'react-json-viewer' {
  import { FC } from 'react';

  export interface ReactJsonProps {
    src: unknown;
    theme?: string;
    collapsed?: boolean;
    displayDataTypes?: boolean;
    displayObjectSize?: boolean;
    // Add other props as needed
  }

  const ReactJson: FC<ReactJsonProps>;
  export default ReactJson;
}