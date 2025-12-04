"""
Calculation CRUD operations and endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Calculation, User
from app.schemas import CalculationCreate, CalculationResponse, CalculationUpdate, Message
from app.operations import calculate, DivisionByZeroError, InvalidOperationError
from app.users import get_current_user_dependency
from app.logger_config import get_logger

logger = get_logger()

router = APIRouter(prefix="/calculations", tags=["calculations"])


@router.post("", response_model=CalculationResponse, status_code=status.HTTP_201_CREATED)
async def add_calculation(
    calculation_data: CalculationCreate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Add (Create) a new calculation.
    
    Requires authentication (JWT token).
    
    - **a**: First operand
    - **b**: Second operand
    - **type**: Operation type (add, subtract, multiply, divide)
    
    Returns the calculation with computed result.
    """
    logger.info(
        f"Creating calculation for user {current_user.username}: "
        f"{calculation_data.a} {calculation_data.type} {calculation_data.b}"
    )
    
    try:
        # Perform the calculation
        result = calculate(calculation_data.a, calculation_data.b, calculation_data.type)
        
        # Create calculation record
        new_calculation = Calculation(
            user_id=current_user.id,
            a=calculation_data.a,
            b=calculation_data.b,
            type=calculation_data.type,
            result=result
        )
        
        db.add(new_calculation)
        db.commit()
        db.refresh(new_calculation)
        
        logger.info(
            f"Calculation created successfully: ID {new_calculation.id}, "
            f"Result: {result}"
        )
        return new_calculation
        
    except DivisionByZeroError as e:
        logger.warning(f"Division by zero attempt: {calculation_data.a} / {calculation_data.b}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Division by zero is not allowed"
        )
    except InvalidOperationError as e:
        logger.warning(f"Invalid operation: {calculation_data.type}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating calculation: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while creating calculation"
        )


@router.get("", response_model=List[CalculationResponse])
async def browse_calculations(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Browse (List) all calculations for the authenticated user.
    
    Requires authentication (JWT token).
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100, max: 1000)
    
    Returns list of calculations belonging to the authenticated user.
    """
    logger.info(
        f"Browsing calculations for user {current_user.username} "
        f"(skip={skip}, limit={limit})"
    )
    
    # Limit the maximum number of results
    limit = min(limit, 1000)
    
    calculations = db.query(Calculation).filter(
        Calculation.user_id == current_user.id
    ).order_by(
        Calculation.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    logger.info(f"Retrieved {len(calculations)} calculations for user {current_user.username}")
    return calculations


@router.get("/{calculation_id}", response_model=CalculationResponse)
async def read_calculation(
    calculation_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Read (Get) a specific calculation by ID.
    
    Requires authentication (JWT token).
    Only returns calculations belonging to the authenticated user.
    
    - **calculation_id**: Calculation ID
    """
    logger.info(
        f"Reading calculation {calculation_id} for user {current_user.username}"
    )
    
    calculation = db.query(Calculation).filter(
        Calculation.id == calculation_id,
        Calculation.user_id == current_user.id
    ).first()
    
    if not calculation:
        logger.warning(
            f"Calculation {calculation_id} not found or doesn't belong to "
            f"user {current_user.username}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calculation not found"
        )
    
    logger.info(f"Calculation {calculation_id} retrieved successfully")
    return calculation


@router.put("/{calculation_id}", response_model=CalculationResponse)
async def edit_calculation(
    calculation_id: int,
    calculation_data: CalculationUpdate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Edit (Update) a calculation.
    
    Requires authentication (JWT token).
    Only allows updating calculations belonging to the authenticated user.
    
    - **calculation_id**: Calculation ID
    - **a**: New first operand (optional)
    - **b**: New second operand (optional)
    - **type**: New operation type (optional)
    
    The result is automatically recalculated when any field is updated.
    """
    logger.info(
        f"Updating calculation {calculation_id} for user {current_user.username}"
    )
    
    calculation = db.query(Calculation).filter(
        Calculation.id == calculation_id,
        Calculation.user_id == current_user.id
    ).first()
    
    if not calculation:
        logger.warning(
            f"Calculation {calculation_id} not found or doesn't belong to "
            f"user {current_user.username}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calculation not found"
        )
    
    # Update fields if provided
    updated = False
    if calculation_data.a is not None:
        calculation.a = calculation_data.a
        updated = True
    if calculation_data.b is not None:
        calculation.b = calculation_data.b
        updated = True
    if calculation_data.type is not None:
        calculation.type = calculation_data.type
        updated = True
    
    if not updated:
        logger.info(f"No fields to update for calculation {calculation_id}")
        return calculation
    
    # Recalculate the result
    try:
        result = calculate(calculation.a, calculation.b, calculation.type)
        calculation.result = result
        
        db.commit()
        db.refresh(calculation)
        
        logger.info(
            f"Calculation {calculation_id} updated successfully. "
            f"New result: {result}"
        )
        return calculation
        
    except DivisionByZeroError:
        logger.warning(
            f"Division by zero in update: {calculation.a} / {calculation.b}"
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Division by zero is not allowed"
        )
    except InvalidOperationError as e:
        logger.warning(f"Invalid operation in update: {calculation.type}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating calculation: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while updating calculation"
        )


@router.patch("/{calculation_id}", response_model=CalculationResponse)
async def edit_calculation_patch(
    calculation_id: int,
    calculation_data: CalculationUpdate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Edit (Partial Update) a calculation using PATCH.
    
    Requires authentication (JWT token).
    Only allows updating calculations belonging to the authenticated user.
    
    - **calculation_id**: Calculation ID
    - **a**: New first operand (optional)
    - **b**: New second operand (optional)
    - **type**: New operation type (optional)
    
    The result is automatically recalculated when any field is updated.
    This endpoint is identical to PUT but follows RESTful conventions for partial updates.
    """
    # Reuse the PUT logic
    return await edit_calculation(calculation_id, calculation_data, current_user, db)


@router.delete("/{calculation_id}", response_model=Message)
async def delete_calculation(
    calculation_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Delete a calculation.
    
    Requires authentication (JWT token).
    Only allows deleting calculations belonging to the authenticated user.
    
    - **calculation_id**: Calculation ID
    """
    logger.info(
        f"Deleting calculation {calculation_id} for user {current_user.username}"
    )
    
    calculation = db.query(Calculation).filter(
        Calculation.id == calculation_id,
        Calculation.user_id == current_user.id
    ).first()
    
    if not calculation:
        logger.warning(
            f"Calculation {calculation_id} not found or doesn't belong to "
            f"user {current_user.username}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calculation not found"
        )
    
    db.delete(calculation)
    db.commit()
    
    logger.info(f"Calculation {calculation_id} deleted successfully")
    return {"message": f"Calculation {calculation_id} deleted successfully"}
