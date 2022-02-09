import React from 'react';
import { styled } from '@mui/material/styles';

const Root = styled('div')(({
  width: '100%',
  height: '100%',
  display: 'flex',
  flexFlow: 'row nowrap',
  justifyContent: 'flex-start',
  alignItems: 'center',
  boxSizing: 'border-box',
}));

function Data() {
  return (
    <Root>
      DATA
    </Root>
  );
}

export default Data;
