#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证模块 - 全局API密钥认证
"""

import os
from fastapi import HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

# 全局API密钥配置
GLOBAL_API_KEY = "PolyNex-PolyOCR-2025xm"
GLOBAL_SECRET = "782b52f0-d5b6-488b-9fdd-0a9026d3a0c0"
GLOBAL_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

# HTTP Bearer认证
security = HTTPBearer()
def verify_api_key(api_key: str) -> bool:
    """
    验证API密钥
    
    Args:
        api_key: 用户提供的API密钥
        
    Returns:
        bool: 验证是否通过
    """
    return api_key == GLOBAL_API_KEY

def verify_secret(secret: str) -> bool:
    """
    验证Secret密钥
    
    Args:
        secret: 用户提供的Secret密钥
        
    Returns:
        bool: 验证是否通过
    """
    return secret == GLOBAL_SECRET

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    获取当前用户（通过Bearer Token认证）
    
    Args:
        credentials: HTTP认证凭据
        
    Returns:
        str: 用户标识
        
    Raises:
        HTTPException: 认证失败时抛出
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="缺少认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证Bearer Token
    if not verify_api_key(credentials.credentials):
        raise HTTPException(
            status_code=401,
            detail="无效的API密钥",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return credentials.credentials

async def get_current_user_by_header(x_api_key: Optional[str] = Header(None)):
    """
    通过Header获取当前用户（通过X-API-Key认证）
    
    Args:
        x_api_key: X-API-Key请求头
        
    Returns:
        str: 用户标识
        
    Raises:
        HTTPException: 认证失败时抛出
    """
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="缺少X-API-Key请求头",
        )
    
    # 验证API Key
    if not verify_api_key(x_api_key):
        raise HTTPException(
            status_code=401,
            detail="无效的API密钥",
        )
    
    return x_api_key

def get_auth_dependency():
    """
    获取认证依赖（支持两种认证方式）
    """
    async def auth_dependency(
        authorization: Optional[str] = Header(None),
        x_api_key: Optional[str] = Header(None)
    ):
        # 优先使用Bearer Token认证
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            if not verify_api_key(token):
                raise HTTPException(
                    status_code=401,
                    detail="无效的API密钥",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return token
        
        # 其次使用X-API-Key认证
        elif x_api_key:
            if not verify_api_key(x_api_key):
                raise HTTPException(
                    status_code=401,
                    detail="无效的API密钥",
                )
            return x_api_key
        
        # 都没有则返回错误
        else:
            raise HTTPException(
                status_code=401,
                detail="缺少认证信息，请提供Authorization: Bearer <api_key>或X-API-Key请求头",
            )
    
    return auth_dependency

# 认证依赖
auth_required = get_auth_dependency()